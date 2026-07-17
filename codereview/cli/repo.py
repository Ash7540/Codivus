import os
import sys
from codereview.reviewer import Reviewer
from codereview.cli.review import output_result


def handle_repo(args, config):
    reviewer = Reviewer(config)
    target_path = os.path.abspath(args.path)

    if not os.path.exists(target_path):
        print(f"Error: Path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(target_path):
        print(
            f"Error: repo command requires a directory target. Use review command for files: {target_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = reviewer.review_dir(target_path)
    except Exception as e:
        print(f"Error executing repository review: {str(e)}", file=sys.stderr)
        sys.exit(1)

    output_result(result, args.format, args.output)


def handle_security(args, config):
    reviewer = Reviewer(config)
    target_path = os.path.abspath(args.path)

    if not os.path.exists(target_path):
        print(f"Error: Path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    try:
        if os.path.isdir(target_path):
            result = reviewer.review_dir(target_path, category_focus="security")
        else:
            result = reviewer.review_file(target_path, category_focus="security")
    except Exception as e:
        print(f"Error executing security scan: {str(e)}", file=sys.stderr)
        sys.exit(1)

    output_result(result, args.format, args.output)
