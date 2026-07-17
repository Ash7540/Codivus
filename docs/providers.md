# LLM Providers

Codivus abstracts provider-specific details to support unified structured requests.

## OpenAI

Ensure `OPENAI_API_KEY` is configured:

```bash
export OPENAI_API_KEY="your-api-key"
```

## Anthropic Claude

Ensure `ANTHROPIC_API_KEY` is configured:

```bash
export ANTHROPIC_API_KEY="your-api-key"
export CODIVUS_PROVIDER="anthropic"
export CODIVUS_MODEL="claude-3-5-sonnet-20240620"
```

## Google Gemini

Ensure `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is configured:

```bash
export GEMINI_API_KEY="your-api-key"
export CODIVUS_PROVIDER="google"
export CODIVUS_MODEL="gemini-1.5-pro"
```

## Ollama (Local)

Run your local Ollama instance and configure host URL:

```bash
export OLLAMA_HOST="http://localhost:11434"
export CODIVUS_PROVIDER="ollama"
export CODIVUS_MODEL="llama3"
```
