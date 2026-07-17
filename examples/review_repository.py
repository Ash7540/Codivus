import os
from codereview.config import Config
from codereview.reviewer import Reviewer


def main():
    # 1. Setup config to use mock provider to keep execution localized
    config = Config(overrides={"default_provider": "mock"})
    reviewer = Reviewer(config)

    # 2. Identify a local directory to review (e.g. codereview package source)
    target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "codereview")

    if not os.path.exists(target_dir):
        print(f"Target directory {target_dir} not found. Defaulting to current dir.")
        target_dir = "."

    print(f"Running recursive directory review on: {target_dir}...")

    try:
        # 3. Trigger folder review
        repo_result = reviewer.review_dir(target_dir)

        # 4. Display Repository Summary Info
        print("\n=== Repository Review Complete ===")
        print(f"Repository Score: {repo_result.overall_score.overall_score}/100")
        print(f"Files Evaluated: {repo_result.summary.total_files}")

        print("\n--- Individual File Statistics ---")
        for filepath, fsum in repo_result.file_reviews.items():
            relpath = os.path.relpath(filepath, target_dir)
            print(f"- {relpath}: {len(fsum.issues)} issues found.")

    except Exception as e:
        print(f"Directory review failed: {e}")


if __name__ == "__main__":
    main()
