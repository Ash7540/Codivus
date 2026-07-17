import subprocess
import os
from typing import List


class GitRepository:
    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)

    def _run_git(self, args: List[str]) -> str:
        try:
            # We run with PAGER=cat or ignore standard output filters
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr.strip()}")

    def is_git_repo(self) -> bool:
        try:
            val = self._run_git(["rev-parse", "--is-inside-work-tree"])
            return val == "true"
        except Exception:
            return False

    def get_staged_files(self) -> List[str]:
        output = self._run_git(
            ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]
        )
        if not output:
            return []
        return [
            os.path.join(self.repo_path, line)
            for line in output.splitlines()
            if line.endswith(".py")
        ]

    def get_unstaged_files(self) -> List[str]:
        output = self._run_git(["diff", "--name-only", "--diff-filter=ACMR"])
        if not output:
            return []
        return [
            os.path.join(self.repo_path, line)
            for line in output.splitlines()
            if line.endswith(".py")
        ]

    def get_staged_diff(self, filepath: str) -> str:
        return self._run_git(["diff", "--cached", "--", filepath])

    def get_unstaged_diff(self, filepath: str) -> str:
        return self._run_git(["diff", "--", filepath])

    def get_files_in_commit(self, commit_hash: str) -> List[str]:
        # Get files changed in specific commit
        output = self._run_git(["show", "--name-only", "--pretty=format:", commit_hash])
        if not output:
            return []
        return [
            os.path.join(self.repo_path, line)
            for line in output.splitlines()
            if line.strip().endswith(".py")
        ]

    def get_commit_diff(self, commit_hash: str, filepath: str) -> str:
        # Get diff of a file in specific commit
        # For a specific commit, we can show diff against parent
        return self._run_git(["show", commit_hash, "--", filepath])

    def get_files_in_diff(self, ref_range: str) -> List[str]:
        output = self._run_git(["diff", "--name-only", "--diff-filter=ACMR", ref_range])
        if not output:
            return []
        return [
            os.path.join(self.repo_path, line)
            for line in output.splitlines()
            if line.strip().endswith(".py")
        ]

    def get_diff_between_refs(self, ref_range: str, filepath: str) -> str:
        return self._run_git(["diff", ref_range, "--", filepath])
