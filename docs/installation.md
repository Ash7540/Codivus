# Installation

Codivus can be installed directly from PyPI.

```bash
pip install codivus
```

## Provider Extras

To install specific LLM provider client SDKs, specify extras targets:

```bash
# Install Anthropic support
pip install codivus[anthropic]

# Install Google Gemini support
pip install codivus[google]

# Install all LLM provider SDKs
pip install codivus[all-providers]
```

## System Requirements

- Python 3.8 or higher.
- Git (optional, required for diff and git-focused audits).
