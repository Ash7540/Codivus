import os
import sys
import importlib.util
from typing import List, Callable
from codereview.plugins.base import BasePlugin
from codereview.models import CodeContext, Issue, ReviewResult

class PluginManager:
    def __init__(self, local_plugins_dir: str = ".codivus/plugins"):
        self.local_plugins_dir = local_plugins_dir
        self.plugins: List[BasePlugin] = []

    def register_plugin(self, plugin: BasePlugin) -> None:
        """Manually registers a plugin instance."""
        if not any(p.name == plugin.name for p in self.plugins):
            self.plugins.append(plugin)

    def load_plugins(self) -> None:
        """Discovers and loads entrypoint and local plugins."""
        # 1. Load entry point package plugins
        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points
                eps = entry_points(group="codivus.plugins")
            else:
                from importlib.metadata import entry_points
                eps = entry_points().get("codivus.plugins", [])

            for ep in eps:
                try:
                    plugin_class = ep.load()
                    self.register_plugin(plugin_class())
                except Exception as e:
                    print(f"Warning: Failed to load entry point plugin {ep.name}: {str(e)}", file=sys.stderr)
        except Exception:
            pass

        # 2. Load local directory plugins
        if os.path.exists(self.local_plugins_dir) and os.path.isdir(self.local_plugins_dir):
            for filename in os.listdir(self.local_plugins_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    filepath = os.path.join(self.local_plugins_dir, filename)
                    module_name = f"codivus_local_plugin_{filename[:-3]}"
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, filepath)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and 
                                    issubclass(attr, BasePlugin) and 
                                    attr is not BasePlugin):
                                    self.register_plugin(attr())
                    except Exception as e:
                        print(f"Warning: Failed to load local plugin {filename}: {str(e)}", file=sys.stderr)

    def get_analysers(self) -> List[Callable[[CodeContext], List[Issue]]]:
        """Gathers static analysers from all loaded plugins."""
        analysers = []
        for plugin in self.plugins:
            try:
                analysers.extend(plugin.get_analysers())
            except Exception as e:
                print(f"Warning: Plugin {plugin.name} get_analysers failed: {str(e)}", file=sys.stderr)
        return analysers

    def modify_prompt(self, context: CodeContext, prompt: str) -> str:
        """Chains prompt modification through all loaded plugins."""
        for plugin in self.plugins:
            try:
                prompt = plugin.modify_prompt(context, prompt)
            except Exception as e:
                print(f"Warning: Plugin {plugin.name} modify_prompt failed: {str(e)}", file=sys.stderr)
        return prompt

    def on_review_start(self, context: CodeContext) -> None:
        """Triggers pre-review hooks on all loaded plugins."""
        for plugin in self.plugins:
            try:
                plugin.on_review_start(context)
            except Exception as e:
                print(f"Warning: Plugin {plugin.name} on_review_start failed: {str(e)}", file=sys.stderr)

    def on_review_end(self, context: CodeContext, result: ReviewResult) -> None:
        """Triggers post-review hooks on all loaded plugins."""
        for plugin in self.plugins:
            try:
                plugin.on_review_end(context, result)
            except Exception as e:
                print(f"Warning: Plugin {plugin.name} on_review_end failed: {str(e)}", file=sys.stderr)
