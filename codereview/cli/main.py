import argparse
import sys
import os
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.cli.report import format_console_report, format_markdown_report, format_json_report

def main():
    parser = argparse.ArgumentParser(
        description="Codivus: AI-assisted Python automated code reviewer."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the file or directory to review (defaults to current directory '.')"
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Only review git staged changes (restricted to modified lines)"
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Only review changes in a specific git commit (restricted to modified lines)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Report output format (text, json, or markdown). Default: text"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optionally save the review report to a file path"
    )
    
    args = parser.parse_args()
    
    # 1. Load config
    config = Config()
    
    # 2. Init reviewer
    reviewer = Reviewer(config)
    
    # 3. Determine run path & execute appropriate review function
    try:
        if args.staged:
            result = reviewer.review_staged(args.path)
        elif args.commit:
            result = reviewer.review_commit(args.commit, args.path)
        else:
            target_path = os.path.abspath(args.path)
            if not os.path.exists(target_path):
                print(f"Error: Path does not exist: {target_path}", file=sys.stderr)
                sys.exit(1)
                
            if os.path.isdir(target_path):
                result = reviewer.review_dir(target_path)
            else:
                result = reviewer.review_file(target_path)
    except Exception as e:
        print(f"Error executing review: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    # 4. Format report output
    if args.format == "json":
        report_content = format_json_report(result)
    elif args.format == "markdown":
        report_content = format_markdown_report(result)
    else:
        report_content = format_console_report(result)
        
    # 5. Output report
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"Report successfully saved to: {args.output}")
        except Exception as e:
            print(f"Error writing report to file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        print(report_content)

if __name__ == "__main__":
    main()
