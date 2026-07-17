# Plugins & Prompts

Configure custom instructions and write plugins to alter review flows.

## Prompt Modifiers

Custom prompt adjustments are generated before querying the provider, allowing custom rules injection:

```python
from codereview.plugins import BasePlugin

class ReactRulesPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "react_rules_plugin"

    def modify_prompt(self, context, prompt: str) -> str:
        # Append specific engineering guidelines
        return prompt + "\n- Ensure all react hooks declare correct dependencies array."
```

## Creating Custom Analysers

Plugins can inject static rules yielding `Issue` lists:

```python
from codereview.plugins import BasePlugin
from codereview.models import Issue, Suggestion

class CustomAnalyserPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "custom_analyser_plugin"

    def get_analysers(self):
        def my_analyser(context):
            issues = []
            if "TODO" in context.source_code:
                issues.append(Issue(
                    title="TODO found",
                    description="Resolve TODO comments before commits.",
                    severity="low",
                    category="style",
                    line_number=1,
                    code_snippet="TODO",
                    suggestion=None
                ))
            return issues
        return [my_analyser]
```
