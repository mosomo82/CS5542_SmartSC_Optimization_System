import json
import pandas as pd
from sklearn.metrics import precision_score, recall_score

def evaluate_system(golden_dataset_path: str, predictions_path: str) -> dict:
    """
    Evaluate system performance against golden dataset.
    """
    with open(golden_dataset_path, 'r') as f:
        golden = json.load(f)

    with open(predictions_path, 'r') as f:
        predictions = json.load(f)

    # Simple evaluation: compare reroute recommendations
    true_labels = [item['should_reroute'] for item in golden]
    pred_labels = [item['predicted_reroute'] for item in predictions]

    precision = precision_score(true_labels, pred_labels)
    recall = recall_score(true_labels, pred_labels)

    results = {
        'precision': precision,
        'recall': recall,
        'f1_score': 2 * (precision * recall) / (precision + recall)
    }

    print(f"Evaluation Results: {results}")
    return results

if __name__ == "__main__":
    # Example usage
    results = evaluate_system("data/golden_dataset.json", "data/predictions.json")
    with open("tests/evaluation_results.json", 'w') as f:
        json.dump(results, f)