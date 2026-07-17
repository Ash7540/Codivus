# Configuration

Codivus uses a unified configuration manager supporting environment overrides, `.env` file settings, and command line overrides.

## Setting Environment Variables

The following parameters are supported:

| Environment Variable | Description | Default |
| --- | --- | --- |
| `CODIVUS_PROVIDER` | Default LLM provider client (`openai`, `anthropic`, `google`, `ollama`, `openrouter`, `azure`) | `openai` |
| `CODIVUS_MODEL` | Specific LLM model to query | `gpt-4o` |
| `CODIVUS_TEMPERATURE` | Sampling temperature for responses | `0.2` |
| `CODIVUS_NO_CACHE` | Set to `1` to disable the review caching engine | `0` |
| `CODIVUS_LOG_LEVEL` | Log levels output (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `WARNING` |

## Configuring via CLI

You can save default configurations locally using CLI commands:

```bash
# View configuration settings
codivus config list

# Set default model
codivus config set default_model gpt-4o-mini
```
