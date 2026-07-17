# Codivus

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Codivus** is an AI-assisted automated code review engine designed for Python codebases. It operates by combining deterministic Abstract Syntax Tree (AST) static analysis with Large Language Models (LLMs) to perform thorough, context-aware code audits, security scanning, and style checking.

---

## Key Features

- **Hybrid Review Engine:** Merges traditional parsing-based static rules with advanced LLM reasoning to ensure zero false positives on basic rules while gaining deep semantic feedback.
- **Provider Abstraction:** Out-of-the-box integrations for OpenAI, Anthropic Claude, Google Gemini, Ollama, OpenRouter, and Azure OpenAI.
- **Execution Caching:** Smart local SHA-256 caching saves execution runtimes and limits API cost by ignoring unchanged files.
- **Extensible Plugins:** Programmatic hooks support custom prompt modifiers, pre-/post-review lifecycle callbacks, and custom static analysers.
- **Git Diffs Integration:** Compare branches, commit ranges, or analyze unstaged/staged git files.
- **Multiple Report Formats:** Export findings as Markdown, HTML, JSON, or SARIF schemas.
- **CLI Commands:** Interactive terminal command suite to run reviews, query settings, and explain code issues.

---

## Installation

Install directly from PyPI:

```bash
pip install codivus
```

### LLM Client Extras

To install specific provider client SDK packages:

```bash
# OpenAI support (default)
pip install codivus

# Anthropic Claude support
pip install codivus[anthropic]

# Google Gemini support
pip install codivus[google]

# Install all SDK libraries
pip install codivus[all-providers]
```

---

## Quickstart

### Programmatic Usage

Create a script `run_review.py` to review a python file:

```python
import os
from codereview.config import Config
from codereview.reviewer import Reviewer

# Load configuration (uses defaults or environment settings)
config = Config()

# Instantiate the reviewer
reviewer = Reviewer(config)

# Execute the review on a file
result = reviewer.review_file("src/main.py")

# Output metrics
print(f"Overall Quality Score: {result.score.overall_score}/100")
print(f"Total Issues Found: {result.summary.total_issues}")

for issue in result.issues:
    print(f"[{issue.severity.upper()}] Line {issue.line_number}: {issue.title}")
    if issue.suggestion:
        print(f"  Proposed Code:\n{issue.suggestion.proposed_code}")
```

### CLI Command Suite

```bash
# Review a single file
codivus review main.py

# Review a directory recursively
codivus repo review src/

# Run a dedicated security audit
codivus security scan main.py

# Explain a code snippet using AI
codivus explain "def hello(): pass"
```

---

## Configuration

Set environment variables in your terminal or a local `.env` file:

```bash
# Select default provider client (openai, anthropic, google, ollama, openrouter, azure)
export CODIVUS_PROVIDER="openai"

# Configure the target model
export CODIVUS_MODEL="gpt-4o"

# Disable review caching (default is enabled)
export CODIVUS_NO_CACHE=0

# Configure logger level (DEBUG, INFO, WARNING, ERROR)
export CODIVUS_LOG_LEVEL="WARNING"
```

---

## Documentation

Full tutorials, design architectures, and API references are available in the [docs/](docs/) directory or can be hosted via MkDocs:

```bash
# Install mkdocs and theme
pip install mkdocs-material

# Start the local docs server
mkdocs serve
```
