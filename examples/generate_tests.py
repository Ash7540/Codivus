import os
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.plugins import BasePlugin
from codereview.models import Issue, Suggestion

# 1. Define custom plugin class
class TodolistTrackerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "todo_list_tracker"

    def get_analysers(self):
        def todo_analyser(context):
            issues = []
            for line_idx, line in enumerate(context.source_code.splitlines(), start=1):
                if "TODO" in line:
                    issues.append(Issue(
                        title="Unresolved TODO Comment",
                        description=f"Plugin tracked a TODO comment: '{line.strip()}'",
                        severity="low",
                        category="style",
                        line_number=line_idx,
                        code_snippet=line,
                        suggestion=None
                    ))
            return issues
        return [todo_analyser]

    def modify_prompt(self, context, prompt: str) -> str:
        return prompt + "\nNOTE: Keep reviews concise. Focus heavily on cleanliness."

def main():
    print("=== Pipeline Plugin Setup Example ===")
    
    # 2. Write a dummy script with TODO comments
    sample_code = """
def process_data(data):
    # TODO: Add exception handling block below
    parsed = int(data)
    return parsed * 2
"""
    temp_file = "temp_sample_todo.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(sample_code.strip())
        
    print(f"Created target script '{temp_file}' containing unresolved TODOs.")

    try:
        # 3. Setup reviewer with mock provider
        config = Config(overrides={"default_provider": "mock"})
        reviewer = Reviewer(config)
        
        # 4. Programmatically register custom plugin
        reviewer.plugin_manager.register_plugin(TodolistTrackerPlugin())
        print("Registered 'todo_list_tracker' plugin successfully.")
        
        # 5. Run review
        result = reviewer.review_file(temp_file)
        
        # 6. Verify custom plugin findings
        todo_issues = [i for i in result.issues if "TODO" in i.title]
        print(f"\nTotal Issues Discovered: {len(result.issues)}")
        print(f"Plugin Analyser TODO Issues Found: {len(todo_issues)}")
        for idx, issue in enumerate(todo_issues, start=1):
            print(f"- Line {issue.line_number}: {issue.description}")

    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Cleaned up temporary target '{temp_file}'.")

if __name__ == "__main__":
    main()
