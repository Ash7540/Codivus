import os
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.git.diff import get_modified_files_and_lines

def main():
    print("=== Git Diff Review Integration ===")
    
    # 1. Check if git repository is initialized
    if not os.path.exists(".git"):
        print("Not a git repository. Skipping git operations.")
        return

    # 2. Get modified files and lines against main branch (or HEAD for local changes)
    try:
        modified_map = get_modified_files_and_lines(base_ref="HEAD~1")
        if not modified_map:
            print("No modifications detected in git history HEAD~1 vs working tree.")
            return
            
        print(f"Discovered {len(modified_map)} modified files in history.")
        
        # 3. Setup reviewer with mock provider
        config = Config(overrides={"default_provider": "mock"})
        reviewer = Reviewer(config)
        
        # 4. Review only modified lines
        for filepath, lines in modified_map.items():
            if os.path.exists(filepath) and filepath.endswith(".py"):
                print(f"\nReviewing {filepath} (modified lines: {lines})...")
                result = reviewer.review_file(filepath, modified_lines=lines)
                print(f"Review Score: {result.score.overall_score}/100")
                print(f"Issues restricted to diff: {len(result.issues)}")
                
    except Exception as e:
        print(f"Failed to query git diff or execute review: {str(e)}")

if __name__ == "__main__":
    main()
