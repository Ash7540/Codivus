# Quickstart

Get started with the Codivus programmatic API in under a minute.

## Basic Usage

Here is how to run a code review on a single Python file:

```python
import os
from codereview.config import Config
from codereview.reviewer import Reviewer

# Load default configurations (e.g. from .env files or environment)
config = Config()

# Instantiate reviewer
reviewer = Reviewer(config)

# Review a Python file
result = reviewer.review_file("src/main.py")

# Output metrics
print(f"Overall Quality Score: {result.score.overall_score}/100")
print(f"Total Issues Discovered: {result.summary.total_issues}")

for issue in result.issues:
    print(f"[{issue.severity.upper()}] Line {issue.line_number}: {issue.title}")
    if issue.suggestion:
        print(f"  Proposed Code:\n{issue.suggestion.proposed_code}")
```

## Running Directory Reviews

You can scan whole directories recursively to generate repository-wide architecture reports:

```python
repo_result = reviewer.review_dir("src/")

print(f"Repository Score: {repo_result.summary.summary_text}")
print(f"Files analyzed: {len(repo_result.file_summaries)}")
```
