# Integrations

Integrate Codivus directly inside your local development cycles and remote workflows.

## Git Pre-Commit Hook

Verify staged changes during commits. Add this pattern to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Ash7540/Codivus
    rev: v1.0.0
    hooks:
      - id: codivus-review
        stages: [commit]
```

## GitHub Actions

Run automated PR reviews on pull request actions. Create `.github/workflows/codivus.yml`:

```yaml
name: Codivus CI Review

on:
  pull_request:
    branches: [main]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install codivus[openai]

      - name: Run diff review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: codivus review --diff origin/main
```
