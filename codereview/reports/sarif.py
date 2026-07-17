import json
from codereview.models import RepositoryReviewResult


def map_severity_to_sarif_level(severity: str) -> str:
    sev = severity.lower()
    if sev in ("critical", "high"):
        return "error"
    elif sev == "medium":
        return "warning"
    else:
        return "note"


def map_category_to_rule_id(category: str) -> str:
    cat = category.lower()
    if cat == "security":
        return "COD-SEC"
    elif cat == "performance":
        return "COD-PERF"
    elif cat == "style":
        return "COD-STYLE"
    else:
        return "COD-BUG"


def export_sarif(result, filepath: str) -> None:
    is_repo = isinstance(result, RepositoryReviewResult)

    # Declare rules
    rules = [
        {
            "id": "COD-SEC",
            "name": "SecurityVulnerability",
            "shortDescription": {
                "text": "Security vulnerability identified by Codivus."
            },
        },
        {
            "id": "COD-PERF",
            "name": "PerformanceIssue",
            "shortDescription": {
                "text": "Performance bottleneck or inefficient pattern."
            },
        },
        {
            "id": "COD-STYLE",
            "name": "StyleViolation",
            "shortDescription": {"text": "Coding style standard or PEP 8 violation."},
        },
        {
            "id": "COD-BUG",
            "name": "LogicalBug",
            "shortDescription": {
                "text": "Logical bug, complexity warning, or cross-file issue."
            },
        },
    ]

    sarif_results = []

    # Process issues
    if is_repo:
        # 1. Process repository-level issues
        for issue in result.repo_issues:
            rule_id = map_category_to_rule_id(issue.category)
            level = map_severity_to_sarif_level(issue.severity)

            sarif_result = {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": f"{issue.title}: {issue.description}"},
                "locations": [],
            }
            sarif_results.append(sarif_result)

        # 2. Process file-level issues
        for rel_file, f_res in result.file_reviews.items():
            for issue in f_res.issues:
                rule_id = map_category_to_rule_id(issue.category)
                level = map_severity_to_sarif_level(issue.severity)

                location = {
                    "physicalLocation": {
                        "artifactLocation": {"uri": rel_file},
                    }
                }

                if issue.line_number and issue.line_number > 0:
                    location["physicalLocation"]["region"] = {
                        "startLine": issue.line_number
                    }

                sarif_result = {
                    "ruleId": rule_id,
                    "level": level,
                    "message": {"text": f"{issue.title}: {issue.description}"},
                    "locations": [location],
                }
                sarif_results.append(sarif_result)
    else:
        # Process single file issues
        # Try to find filepath from the result context or fallback to dummy
        # In single file ReviewResult, context is not directly attached but filename is in summary.
        # So we can use a fallback filename.
        filename = "reviewed_file.py"
        for issue in result.issues:
            rule_id = map_category_to_rule_id(issue.category)
            level = map_severity_to_sarif_level(issue.severity)

            location = {
                "physicalLocation": {
                    "artifactLocation": {"uri": filename},
                }
            }

            if issue.line_number and issue.line_number > 0:
                location["physicalLocation"]["region"] = {
                    "startLine": issue.line_number
                }

            sarif_result = {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": f"{issue.title}: {issue.description}"},
                "locations": [location],
            }
            sarif_results.append(sarif_result)

    # Complete SARIF structure
    sarif_log = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Codivus",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/Ash7540/Codivus",
                        "rules": rules,
                    }
                },
                "results": sarif_results,
            }
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sarif_log, f, indent=2)
