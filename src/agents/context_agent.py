"""
context_agent.py — ReMindRAG Retrieval + [RETRIEVED CONSTRAINTS] Injection
===========================================================================
Implements the Context layer of the CPP pipeline.

Responsibilities:
  1. ReMindRAG Retrieval — semantic vector search against
     HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED using
     Snowflake Cortex EMBED_TEXT_768.  seed=42 is baked into the
     ORDER BY tiebreaker so results are deterministic across identical
     queries.

  2. [RETRIEVED CONSTRAINTS] Block — assembles retrieved chunks into a
     structured evidence block that is injected into the LLM prompt.
     Format follows the Lab 8 CPP specification:

         [RETRIEVED CONSTRAINTS]
         1. <RECORD_TYPE> | <CHUNK_ID>
            <TEXT_CONTENT>
         2. ...
         [END RETRIEVED CONSTRAINTS]

     The block is appended to any caller-supplied prompt template so the
     model is explicitly instructed to use retrieved evidence rather than
     recalling from parametric memory.

Usage:
    from src.agents.context_agent import retrieve_context, build_constrained_prompt

    # 1. Retrieve top-k relevant chunks
    ctx = retrieve_context(session, query="bridge weight limit Chicago route", top_k=5)

    # 2. Inject into a prompt
    prompt = build_constrained_prompt(
        base_prompt="You are a logistics routing expert.",
        user_query="Is I-55 safe for a 40-ton truck?",
        context=ctx,
    )

    # 3. Pass prompt to Cortex / cpp_agent
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Any, List

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Embedding model — must match whichever model was used to populate the column
_EMBED_MODEL = "snowflake-arctic-embed-m"

# Default number of chunks to retrieve
_DEFAULT_TOP_K = 5

# Deterministic seed for tiebreaking (ReMindRAG spec: seed=42)
_SEED = 42

# Snowflake Cortex vector similarity function available since 2024-Q3
_VECTOR_COSINE_SQL = "VECTOR_COSINE_SIMILARITY"


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RetrievedChunk:
    """A single retrieved chunk from SILVER.LOGISTICS_VECTORIZED.

    Attributes:
        chunk_id:     Primary-key identifier of the chunk.
        record_type:  Source record category (load, trip, safety, etc.)
        text_content: Human-readable text content of the chunk.
        score:        Cosine similarity score (0–1, higher = more relevant).
    """
    chunk_id: str
    record_type: str
    text_content: str
    score: float


@dataclass
class RetrievalContext:
    """Result of a ReMindRAG retrieval pass.

    Attributes:
        query:        The original query string.
        top_k:        Number of chunks requested.
        chunks:       Ordered list of retrieved chunks (highest score first).
        seed:         Random seed used for deterministic tiebreaking.
        constraints_block: Pre-rendered [RETRIEVED CONSTRAINTS] block string.
    """
    query: str
    top_k: int
    chunks: List[RetrievedChunk] = field(default_factory=list)
    seed: int = _SEED
    constraints_block: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# SQL templates
# ─────────────────────────────────────────────────────────────────────────────

# Primary path: EMBEDDING column is populated → use Cortex vector cosine search.
# The tiebreaker RANDOM(seed) ensures deterministic ordering for equal scores.
_SQL_VECTOR_SEARCH = """
SELECT
    CHUNK_ID,
    RECORD_TYPE,
    TEXT_CONTENT,
    {similarity_fn}(
        EMBEDDING,
        SNOWFLAKE.CORTEX.EMBED_TEXT_768('{embed_model}', '{query_escaped}')
    ) AS SCORE
FROM HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED
WHERE EMBEDDING IS NOT NULL
ORDER BY SCORE DESC, RANDOM({seed}) ASC
LIMIT {top_k}
"""

# Fallback path: EMBEDDING column not yet populated → full-text keyword search.
# Uses ILIKE for broad matching; ordered by record type then seeded random.
_SQL_KEYWORD_FALLBACK = """
SELECT
    CHUNK_ID,
    RECORD_TYPE,
    TEXT_CONTENT,
    0.0 AS SCORE
FROM HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED
WHERE {search_condition}
ORDER BY RECORD_TYPE, RANDOM({seed}) ASC
LIMIT {top_k}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Constraints block renderer
# ─────────────────────────────────────────────────────────────────────────────

def _render_constraints_block(chunks: List[RetrievedChunk]) -> str:
    """Render retrieved chunks as a [RETRIEVED CONSTRAINTS] evidence block.

    The block format follows the Lab 8 CPP specification so the LLM is
    explicitly instructed to use evidence rather than parametric memory:

        [RETRIEVED CONSTRAINTS]
        1. safety | CHUNK_42
           Safety incident: speeding involving driver D001 on 2023-04-11.
        2. load | CHUNK_17
           Load L005: Chicago → St. Louis, 312 miles, revenue $4200, ...
        [END RETRIEVED CONSTRAINTS]
    """
    if not chunks:
        return (
            "[RETRIEVED CONSTRAINTS]\n"
            "(No relevant logistics records found for this query.)\n"
            "[END RETRIEVED CONSTRAINTS]"
        )

    lines = ["[RETRIEVED CONSTRAINTS]"]
    for i, chunk in enumerate(chunks, start=1):
        score_tag = f" (score: {chunk.score:.4f})" if chunk.score > 0.0 else ""
        lines.append(f"{i}. {chunk.record_type} | {chunk.chunk_id}{score_tag}")
        # Indent the text content under the header line
        for text_line in chunk.text_content.strip().splitlines():
            lines.append(f"   {text_line}")
    lines.append("[END RETRIEVED CONSTRAINTS]")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Core retrieval function
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_context(
    session: Any,
    query: str,
    top_k: int = _DEFAULT_TOP_K,
    seed: int = _SEED,
) -> RetrievalContext:
    """ReMindRAG retrieval from SILVER.LOGISTICS_VECTORIZED.

    Attempts a Cortex EMBED_TEXT_768 vector cosine search first.
    Falls back to keyword (ILIKE) search if the EMBEDDING column is
    not yet populated (e.g., in fresh-pipeline environments).

    seed=42 is used as the RANDOM() tiebreaker so identical queries always
    return the same ranked list — required by the Lab 9 ReMindRAG spec.

    Args:
        session:  Active Snowflake Snowpark Session.
        query:    Natural-language query to retrieve evidence for.
        top_k:    Maximum number of chunks to return (default: 5).
        seed:     Tiebreaker seed for deterministic ordering (default: 42).

    Returns:
        RetrievalContext with chunks and pre-rendered constraints_block.
    """
    logger.info(
        "[ContextAgent] ReMindRAG retrieval: query=%r  top_k=%d  seed=%d",
        query[:80], top_k, seed,
    )

    # Sanitise query for SQL embedding (no f-string injection risk for the
    # Cortex call — the query goes inside a string literal parameter)
    query_escaped = query.replace("'", "\\'").replace("\\", "\\\\")

    chunks: List[RetrievedChunk] = []

    # ── Attempt 1: vector cosine search (requires populated EMBEDDING col) ────
    try:
        vector_sql = _SQL_VECTOR_SEARCH.format(
            similarity_fn=_VECTOR_COSINE_SQL,
            embed_model=_EMBED_MODEL,
            query_escaped=query_escaped,
            seed=seed,
            top_k=top_k,
        )
        rows = session.sql(vector_sql).collect()

        if rows:
            chunks = [
                RetrievedChunk(
                    chunk_id=str(row["CHUNK_ID"]),
                    record_type=str(row["RECORD_TYPE"]),
                    text_content=str(row["TEXT_CONTENT"]),
                    score=float(row["SCORE"]) if row["SCORE"] is not None else 0.0,
                )
                for row in rows
            ]
            logger.info(
                "[ContextAgent] Vector search returned %d chunk(s) "
                "(top score=%.4f).",
                len(chunks), chunks[0].score if chunks else 0.0,
            )
        else:
            logger.info(
                "[ContextAgent] Vector search returned 0 results — "
                "EMBEDDING column may not be populated. Falling back to keyword search."
            )

    except Exception as exc:
        logger.warning(
            "[ContextAgent] Vector search failed (%s). "
            "Falling back to keyword search.", exc,
        )

    # ── Attempt 2: keyword fallback (no EMBEDDING required) ──────────────────
    if not chunks:
        keywords = [w for w in query.split() if len(w) >= 4][:6]
        if keywords:
            def _safe_kw(kw: str) -> str:
                return kw.replace("'", "\\'").replace("%", "\\%")
            conditions = " OR ".join(
                "TEXT_CONTENT ILIKE '%" + _safe_kw(kw) + "%'"
                for kw in keywords
            )
        else:
            conditions = "1=1"  # return any rows if query has no long words

        fallback_sql = _SQL_KEYWORD_FALLBACK.format(
            search_condition=conditions,
            seed=seed,
            top_k=top_k,
        )
        try:
            rows = session.sql(fallback_sql).collect()
            chunks = [
                RetrievedChunk(
                    chunk_id=str(row["CHUNK_ID"]),
                    record_type=str(row["RECORD_TYPE"]),
                    text_content=str(row["TEXT_CONTENT"]),
                    score=0.0,
                )
                for row in rows
            ]
            logger.info(
                "[ContextAgent] Keyword fallback returned %d chunk(s).",
                len(chunks),
            )
        except Exception as exc:
            logger.error(
                "[ContextAgent] Keyword fallback also failed: %s", exc,
            )

    # ── Build constraints block ───────────────────────────────────────────────
    constraints_block = _render_constraints_block(chunks)
    logger.debug("[ContextAgent] Constraints block:\n%s", constraints_block)

    return RetrievalContext(
        query=query,
        top_k=top_k,
        chunks=chunks,
        seed=seed,
        constraints_block=constraints_block,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builder — injects [RETRIEVED CONSTRAINTS] into a prompt template
# ─────────────────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """{base_prompt}

{constraints_block}

INSTRUCTION: You MUST ground your answer in the [RETRIEVED CONSTRAINTS] above.
Do NOT rely on your parametric memory for logistics facts, bridge limits, or
route-specific data. If the retrieved constraints do not contain relevant
information, explicitly state that no relevant records were found.

User Query: {user_query}
"""


def build_constrained_prompt(
    base_prompt: str,
    user_query: str,
    context: RetrievalContext,
) -> str:
    """Inject the [RETRIEVED CONSTRAINTS] evidence block into a prompt template.

    Args:
        base_prompt:  System/role description for the LLM (e.g.,
                      "You are a logistics routing expert for HyperLogistics.").
        user_query:   The end-user's natural-language question.
        context:      RetrievalContext returned by retrieve_context().

    Returns:
        Fully assembled prompt string ready to pass to Cortex COMPLETE.
    """
    prompt = _PROMPT_TEMPLATE.format(
        base_prompt=base_prompt.strip(),
        constraints_block=context.constraints_block,
        user_query=user_query.strip(),
    )
    logger.debug(
        "[ContextAgent] Built constrained prompt (%d chars, %d chunk(s)).",
        len(prompt), len(context.chunks),
    )
    return prompt
