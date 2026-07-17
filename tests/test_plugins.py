from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.plugins import BasePlugin, PluginManager
from codereview.models import CodeContext, Issue, Suggestion, ReviewResult


class CustomTestPlugin(BasePlugin):
    def __init__(self):
        self.start_called = False
        self.end_called = False
        self.received_prompt = ""

    @property
    def name(self) -> str:
        return "custom_test_plugin"

    def get_analysers(self):
        def test_analyser(context: CodeContext):
            return [
                Issue(
                    title="Plugin Issue",
                    description="Custom issue detected by plugin.",
                    severity="high",
                    category="bug",
                    line_number=1,
                    code_snippet="print('test')",
                    suggestion=Suggestion(
                        original_code="print('test')",
                        proposed_code="print('custom')",
                        explanation="Plugin enhancement.",
                    ),
                )
            ]

        return [test_analyser]

    def modify_prompt(self, context: CodeContext, prompt: str) -> str:
        self.received_prompt = prompt
        return prompt + "\n# Modified by CustomTestPlugin"

    def on_review_start(self, context: CodeContext) -> None:
        self.start_called = True

    def on_review_end(self, context: CodeContext, result: ReviewResult) -> None:
        self.end_called = True


def test_manual_plugin_registration(tmp_path):
    config = Config(overrides={"default_provider": "mock"})
    reviewer = Reviewer(config)

    # Register our test plugin
    plugin = CustomTestPlugin()
    reviewer.plugin_manager.register_plugin(plugin)

    # Setup a mock target file to review
    target_file = tmp_path / "test_file.py"
    target_file.write_text("print('hello')", encoding="utf-8")

    # Inject a print statement mock or intercept modify_prompt to check prompt modification
    # We patch generate_review on MockProvider to assert prompt_modifier was run
    original_generate_review = reviewer.provider.generate_review

    def generate_review_spy(
        code_context,
        static_issues=None,
        modified_lines=None,
        category_focus=None,
        prompt_modifier=None,
    ):
        if prompt_modifier:
            # Trigger the modifier so we can check it
            prompt_modifier("test prompt")
        return original_generate_review(
            code_context, static_issues, modified_lines, category_focus, prompt_modifier
        )

    reviewer.provider.generate_review = generate_review_spy

    # Execute review
    result = reviewer.review_file(str(target_file))

    # Assertions
    assert plugin.start_called is True
    assert plugin.end_called is True
    assert "test prompt" in plugin.received_prompt

    # Assert custom analyser issue is present in results
    plugin_issues = [i for i in result.issues if i.title == "Plugin Issue"]
    assert len(plugin_issues) == 1
    assert plugin_issues[0].severity == "high"


def test_local_directory_plugin_loading(tmp_path):
    # Create a local plugins directory
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Create a mock plugin file
    plugin_code = """
from codereview.plugins import BasePlugin

class DirectoryMockPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "directory_mock_plugin"
"""
    (plugins_dir / "my_plugin.py").write_text(plugin_code, encoding="utf-8")

    # Load plugins via PluginManager pointing to the temp plugins directory
    manager = PluginManager(local_plugins_dir=str(plugins_dir))
    manager.load_plugins()

    # Assert that the plugin was loaded and registered successfully
    loaded_plugin_names = [p.name for p in manager.plugins]
    assert "directory_mock_plugin" in loaded_plugin_names
