# Codivus

Codivus is a powerful, AI-assisted Python automated code review engine. It combines deterministic AST-based static analysis with state-of-the-art Large Language Models (LLMs) to perform thorough, context-aware code assessments and generate high-fidelity suggestions.

## Key Features

- **Hybrid Analysis:** Combines deterministic static syntax/style/security parsing with LLM-based reasoning.
- **Multi-Provider LLM Wrapper:** Native integrations for OpenAI, Anthropic, Google Gemini, Ollama, OpenRouter, and Azure OpenAI.
- **Git Integration:** Compare branch diffs, commit changes, or audit only unstaged/staged modifications.
- **Robust Caching:** SHA-256 local result caching prevents redundant LLM queries and saves API expenses.
- **Plugin System:** Extend review pipelines with custom analysers, hooks, and prompt filters.
- **Multiple Report Formats:** Export findings as Markdown, HTML, JSON, and SARIF dashboards.
- **Flexible CLI:** Interactive subcommands for review, configuration, repository summary, security, and explaining issues.
