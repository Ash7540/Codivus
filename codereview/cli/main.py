import argparse
import sys
from codereview.config import Config


def main():
    # Backward compatibility rewrite:
    subcommands = {"review", "repo", "security", "diff", "config", "report"}
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg not in subcommands and first_arg not in {
            "-h",
            "--help",
            "-v",
            "--version",
        }:
            sys.argv.insert(1, "review")
    else:
        sys.argv.append("review")

    parser = argparse.ArgumentParser(
        description="Codivus: AI-assisted Python automated code reviewer command suite."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. review parser
    review_parser = subparsers.add_parser("review", help="Review a file or directory")
    review_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the file or directory to review (defaults to '.')",
    )
    review_parser.add_argument(
        "--staged",
        action="store_true",
        help="Only review git staged changes (restricted to modified lines)",
    )
    review_parser.add_argument(
        "--commit",
        type=str,
        help="Only review changes in a specific git commit (restricted to modified lines)",
    )
    review_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html", "sarif", "pdf"],
        default="text",
        help="Report output format. Default: text",
    )
    review_parser.add_argument("--output", type=str, help="Save report to file path")

    # 2. repo parser
    repo_parser = subparsers.add_parser("repo", help="Perform repository-wide review")
    repo_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the repository directory to review (defaults to '.')",
    )
    repo_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html", "sarif", "pdf"],
        default="text",
        help="Report output format. Default: text",
    )
    repo_parser.add_argument("--output", type=str, help="Save report to file path")

    # 3. security parser
    security_parser = subparsers.add_parser(
        "security", help="Scan codebase specifically for security vulnerabilities"
    )
    security_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to file or directory to scan (defaults to '.')",
    )
    security_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html", "sarif", "pdf"],
        default="text",
        help="Report output format. Default: text",
    )
    security_parser.add_argument("--output", type=str, help="Save report to file path")

    # 4. diff parser
    diff_parser = subparsers.add_parser(
        "diff", help="Review differences between git references"
    )
    diff_parser.add_argument(
        "ref_range",
        help="Git ref range to compare (e.g. 'main...feature' or 'HEAD~1..HEAD')",
    )
    diff_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the repository directory (defaults to '.')",
    )
    diff_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html", "sarif", "pdf"],
        default="text",
        help="Report output format. Default: text",
    )
    diff_parser.add_argument("--output", type=str, help="Save report to file path")

    # 5. config parser
    config_parser = subparsers.add_parser(
        "config", help="View or modify local configuration"
    )
    config_parser.add_argument(
        "config_subcommand",
        choices=["init", "show", "set"],
        help="Config subcommand: init (create default .env), show (display keys), set (write key value)",
    )
    config_parser.add_argument(
        "key", nargs="?", help="Config key name (required for set)"
    )
    config_parser.add_argument(
        "value", nargs="?", help="Config key value (required for set)"
    )

    # 6. report parser
    report_parser = subparsers.add_parser(
        "report", help="Convert an existing JSON report to other formats"
    )
    report_parser.add_argument(
        "json_file", help="Path to the existing JSON review report"
    )
    report_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "html", "sarif", "pdf"],
        default="text",
        help="Target format to export. Default: text",
    )
    report_parser.add_argument(
        "--output", type=str, help="Save converted report to file path"
    )

    args = parser.parse_args()

    # Load configuration
    config = Config()

    # Route subcommands
    if args.command == "review":
        from codereview.cli.review import handle_review

        handle_review(args, config)
    elif args.command == "repo":
        from codereview.cli.repo import handle_repo

        handle_repo(args, config)
    elif args.command == "security":
        from codereview.cli.repo import handle_security

        handle_security(args, config)
    elif args.command == "diff":
        from codereview.cli.diff import handle_diff

        handle_diff(args, config)
    elif args.command == "config":
        from codereview.cli.explain import handle_config

        handle_config(args, config)
    elif args.command == "report":
        from codereview.cli.review import handle_report

        handle_report(args, config)


if __name__ == "__main__":
    main()
