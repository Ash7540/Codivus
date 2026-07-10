import os
import subprocess
import pytest
from codereview.config import Config
from codereview.git.diff import parse_diff_added_lines
from codereview.git.repository import GitRepository
from codereview.reviewer import Reviewer
from codereview.models import RepositoryReviewResult

def test_diff_parser():
    diff_text = """diff --git a/a.py b/a.py
index e69de29..4a07a1b 100644
--- a/a.py
+++ b/a.py
@@ -1,3 +1,6 @@
 import sys
-print("hello")
+print("hello world")
+x = 1
+y = 2
+print(x + y)
"""
    added = parse_diff_added_lines(diff_text)
    # The diff starts at +1, which is line 1 (import sys).
    # Line 2 was deleted (print("hello")).
    # Lines 2, 3, 4, 5 were added/modified in the new file.
    # Let's verify line numbering.
    # Original line 1: import sys (context line)
    # Original line 2: print("hello") (deleted)
    # Added line 2: print("hello world")
    # Added line 3: x = 1
    # Added line 4: y = 2
    # Added line 5: print(x + y)
    # Remaining context lines (none).
    assert added == {2, 3, 4, 5}

def test_git_repository_and_reviewer_flow(tmp_path):
    # Initialize a real Git repository in tmp_path
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Run git init
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True)
    # Set basic local config to prevent git commit failures in environment
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir), check=True)
    
    # 1. Verify is_git_repo
    repo = GitRepository(str(repo_dir))
    assert repo.is_git_repo() is True
    
    # 2. Add a file and stage it
    a_file = repo_dir / "a.py"
    a_file.write_text('"""Module A."""\nimport os\n\ndef my_func():\n    pass\n', encoding="utf-8")
    
    subprocess.run(["git", "add", "a.py"], cwd=str(repo_dir), check=True)
    
    # Verify staged files
    staged = repo.get_staged_files()
    assert len(staged) == 1
    assert os.path.basename(staged[0]) == "a.py"
    
    # Verify staged diff
    staged_diff = repo.get_staged_diff(staged[0])
    assert "+++ b/a.py" in staged_diff
    
    added_lines = parse_diff_added_lines(staged_diff)
    # The entire file is new, so lines 1, 2, 3, 4, 5 are all added
    assert added_lines == {1, 2, 3, 4, 5}
    
    # 3. Commit it and make a second modification (unstaged)
    subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(repo_dir), check=True)
    
    # Get head commit hash
    commit_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo_dir), capture_output=True, text=True, check=True).stdout.strip()
    
    # Verify files in commit
    commit_files = repo.get_files_in_commit(commit_hash)
    assert len(commit_files) == 1
    assert os.path.basename(commit_files[0]) == "a.py"
    
    # Modify file again
    a_file.write_text('"""Module A."""\nimport os\n\ndef my_func():\n    print("new modification")\n', encoding="utf-8")
    
    unstaged = repo.get_unstaged_files()
    assert len(unstaged) == 1
    assert os.path.basename(unstaged[0]) == "a.py"
    
    unstaged_diff = repo.get_unstaged_diff(unstaged[0])
    assert "print(\"new modification\")" in unstaged_diff
    
    # 4. Review staged changes using Reviewer with Mock Provider
    # Currently no files are staged (we committed them and the new changes are unstaged)
    config = Config({"default_provider": "mock", "openai_api_key": "fake"})
    reviewer = Reviewer(config)
    
    staged_result = reviewer.review_staged(str(repo_dir))
    assert staged_result.summary.total_files == 0
    
    # Stage the new changes
    subprocess.run(["git", "add", "a.py"], cwd=str(repo_dir), check=True)
    
    # Now review staged changes
    staged_result = reviewer.review_staged(str(repo_dir))
    assert staged_result.summary.total_files == 1
    
    # The review should only focus on line 5 (the print statement)
    file_review = staged_result.file_reviews["a.py"]
    # The MockProvider returns a Mock Styling Issue at line 1.
    # Since we filtered to modified lines (line 5 in the new staged diff), the mock issue at line 1 should be filtered out!
    # Let's verify: modified_lines is {5}.
    # So line_number=1 is NOT in {5}, so it is filtered out.
    # So the issues list should be empty!
    assert len(file_review.issues) == 0
    
    # 5. Commit second change and review commit
    subprocess.run(["git", "commit", "-m", "second commit"], cwd=str(repo_dir), check=True)
    second_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo_dir), capture_output=True, text=True, check=True).stdout.strip()
    
    commit_result = reviewer.review_commit(second_hash, str(repo_dir))
    assert commit_result.summary.total_files == 1
    assert len(commit_result.file_reviews["a.py"].issues) == 0
