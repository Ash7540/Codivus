import json
from codereview.models import ReviewResult, RepositoryReviewResult


def export_json(result, filepath: str) -> None:
    """
    Exports the review result to a JSON file.
    """
    if isinstance(result, (ReviewResult, RepositoryReviewResult)):
        data = result.model_dump()
    else:
        raise ValueError("Unsupported result type for JSON export.")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
