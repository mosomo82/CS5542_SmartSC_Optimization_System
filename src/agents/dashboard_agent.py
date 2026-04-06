"""
dashboard_agent.py — Snowflake Cortex 9-Tool LangChain Agent
============================================================
Replaces the zero-shot Cortex SQL chat with a true ReAct agent 
capable of autonomous multi-step reasoning using 9 logistics tools.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from langchain_core.language_models.llms import LLM
from langchain_core.tools import tool

# Robust LangChain imports for compatibility across 0.1.x, 0.2.x, and 0.3.x
try:
    # Try the most common 0.1/0.2 entry points
    from langchain.agents import AgentExecutor, initialize_agent, AgentType
except ImportError:
    try:
        # Try explicit module paths (often more reliable in 0.2+)
        from langchain.agents.agent import AgentExecutor
        from langchain.agents.initialize import initialize_agent
        from langchain.agents.agent_types import AgentType
    except ImportError:
        try:
            # Try community fallbacks if the base package is stripped
            from langchain_community.agent_toolkits import AgentExecutor # less likely
            from langchain.agents import AgentExecutor
        except ImportError:
            # Last resort: Define dummies to prevent startup crash, 
            # though execution will fail later.
            logger.error("Failed to import essential LangChain Agent components. Please run 'pip install -r requirements.txt'")
            AgentExecutor = Any 
            initialize_agent = Any
            AgentType = type('AgentType', (), {'STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION': 'structured-chat-zero-shot-react-description'})


from src.agents.compliance_agent import check_route_compliance
from src.agents.efficiency_agent import evaluate_route_risk

class SnowflakeCortexLLM(LLM):
    """Custom LangChain LLM wrapper proxying generation through SNOWFLAKE.CORTEX.COMPLETE."""
    session: Any
    model: str = "llama3.1-70b"
    
    @property
    def _llm_type(self) -> str:
        return "snowflake_cortex"
        
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        clean_prompt = prompt.replace("'", "''") 
        try:
            sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model}', '{clean_prompt}')"
            row = self.session.sql(sql).collect()
            text = row[0][0] if row else ""
            
            if stop:
                for s in stop:
                    if s in text:
                        text = text[:text.index(s)]
                        
            return text
        except Exception as e:
            logger.error("[CortexLLM] SQL Error: %s", e)
            return f"Error: {e}"

def run_cortex_agent(session: Any, user_query: str) -> Dict[str, Any]:
    """
    Initializes the local Snowflake Cortex agent with 9 tools bound to the active session,
    executes the ReAct loop natively via SQL, and returns the reasoning trace.
    """
    
    # ── Tool Definitions (closure over `session` so LLM doesn't need to pass it) ──

    @tool
    def get_fleet_status(limit: int = 5) -> str:
        """Queries SILVER.CLEANED_LOGISTICS for active shipments and delivery status."""
        try:
            sql = f"SELECT ORDER_ID, SHIPPING_MODE, LATE_DELIVERY_RISK FROM HYPERLOGISTICS_DB.SILVER.CLEANED_LOGISTICS LIMIT {limit}"
            return str(session.sql(sql).collect())
        except Exception as e:
            return f"Error: {e}"

    @tool
    def verify_route_compliance(route_wkt: str, vehicle_weight_tons: float, vehicle_height_mt: float) -> str:
        """Use this to check if a route crosses any bridges that violate the truck's weight or height limits."""
        res = check_route_compliance(session, route_wkt, vehicle_weight_tons, vehicle_height_mt)
        return f"Verdict: {res.verdict}. Reason: {res.veto_reason}. Bridges: {res.intersecting_count}"

    @tool
    def get_weather_alerts(city: str) -> str:
        """Queries SILVER.WEATHER_ALERTS for extreme weather anomalies near a city."""
        try:
            sql = f"SELECT WEATHER_ALERT, ALERT_DESCRIPTION FROM HYPERLOGISTICS_DB.SILVER.WEATHER_ALERTS WHERE STATION ILIKE '%{city}%' LIMIT 3"
            return str(session.sql(sql).collect())
        except Exception as e:
            return f"Error: {e}"

    @tool
    def get_safety_heatmap(city: str, state: str) -> str:
        """Queries SILVER.RISK_HEATMAP for historical accident severity in a specific city/state."""
        try:
            sql = f"SELECT INCIDENT_COUNT, AVG_SEVERITY FROM HYPERLOGISTICS_DB.SILVER.RISK_HEATMAP WHERE CITY ILIKE '%{city}%' AND STATE ILIKE '%{state}%' LIMIT 1"
            return str(session.sql(sql).collect())
        except Exception as e:
            return f"Error: {e}"

    @tool
    def evaluate_srsnet_risk(route_wkt: str, context: str) -> str:
        """Invokes the SRSNet Risk Forecasting module to get a holistic route risk score (0.0=Safe, 1.0=Dangerous)."""
        res = evaluate_route_risk(session, route_wkt, context)
        return f"Risk Score: {res.risk_score:.2f} ({res.recommendation}). Factors: {res.risk_factors}. Do not repeat the route geometry in your answer."

    @tool
    def search_knowledge_base(query: str) -> str:
        """Performs ReMindRAG vector search on logistics regulatory handbooks and DOT manuals."""
        try:
            sql = f"""
            SELECT TEXT_CONTENT FROM HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED 
            WHERE TEXT_CONTENT ILIKE '%{query}%' LIMIT 2
            """
            return str(session.sql(sql).collect())
        except Exception as e:
            return f"Error: {e}"

    @tool
    def calculate_eta(distance_miles: float, avg_speed_mph: float = 55.0) -> str:
        """Basic calculation tool to estimate transit time."""
        if avg_speed_mph <= 0: return "Speed must be > 0"
        return f"Estimated transit time: {distance_miles / avg_speed_mph:.1f} hours"

    @tool
    def get_fuel_costs(route_id: str) -> str:
        """Queries BRONZE.LOGISTICS for average fuel costs associated with a specific route or trip."""
        try:
            sql = f"SELECT AVG(FUEL_COST), AVG(FUEL_GALLONS) FROM HYPERLOGISTICS_DB.BRONZE.LOGISTICS WHERE ROUTE_ID = '{route_id}'"
            return str(session.sql(sql).collect())
        except Exception as e:
            return f"Error: {e}"

    @tool
    def get_supplier_delays() -> str:
        """Queries SILVER.CLEANED_LOGISTICS for global late delivery risk propensities."""
        try:
            sql = "SELECT AVG(LATE_DELIVERY_RISK) AS global_risk FROM HYPERLOGISTICS_DB.SILVER.CLEANED_LOGISTICS"
            return str(session.sql(sql).collect())
        except Exception as e:
            return f"Error: {e}"

    tools = [
        get_fleet_status, verify_route_compliance, get_weather_alerts, 
        get_safety_heatmap, evaluate_srsnet_risk, search_knowledge_base, 
        calculate_eta, get_fuel_costs, get_supplier_delays
    ]

    # ── Agent Orchestration ──
    try:
        llm = SnowflakeCortexLLM(session=session)

        prefix = (
            "You are HyperLogistics, an expert logistics dispatch assistant. "
            "When answering queries:\n"
            "- NEVER include raw WKT geometry (LINESTRING/POINT coordinates) in your final answer. "
            "Translate coordinates to human-readable highway names (e.g. 'I-90/94 near downtown Chicago').\n"
            "- Express risk scores with context: low (<0.4), moderate (0.4–0.7), high (>0.7).\n"
            "- Always end with a concrete recommendation: which route to use or avoid and why.\n"
            "- Be concise but specific. Cite the data source (heatmap, weather, bridge check) that drove each conclusion.\n"
        )

        agent_executor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            agent_kwargs={"prefix": prefix}
        )
        
        response = agent_executor.invoke({"input": user_query})
        
        # Format the reasoning trace for the UI
        steps = []
        for action, observation in response.get("intermediate_steps", []):
            steps.append({
                "tool": action.tool,
                "tool_input": str(action.tool_input),
                "observation": str(observation)[:500] + ("..." if len(str(observation)) > 500 else "")
            })
            
        return {
            "output": response.get("output", "No response generated."),
            "trace": steps
        }
    except Exception as exc:
        logger.error("[Cortex Agent] Execution failed: %s", exc)
        return {
            "output": f"Cortex Agent encountered an error: {str(exc)}",
            "trace": []
        }
