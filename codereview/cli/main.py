import argparse
import sys
import os
import tempfile
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.cli.report import format_console_report, format_markdown_report, format_json_report
from codereview.reports import export_json, export_markdown, export_html, export_sarif, export_pdf

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
        choices=["text", "json", "markdown", "html", "sarif", "pdf"],
        default="text",
        help="Report output format (text, json, markdown, html, sarif, or pdf). Default: text"
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
        
    # 4. Handle PDF output constraint
    if args.format == "pdf" and not args.output:
        print("Error: PDF format requires an --output file path.", file=sys.stderr)
        sys.exit(1)

    # 5. Output report (file or stdout)
    if args.output:
        try:
            if args.format == "json":
                export_json(result, args.output)
            elif args.format == "markdown":
                export_markdown(result, args.output)
            elif args.format == "html":
                export_html(result, args.output)
            elif args.format == "sarif":
                export_sarif(result, args.output)
            elif args.format == "pdf":
                export_pdf(result, args.output)
            else:
                # Text format
                report_content = format_console_report(result)
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report_content)
            print(f"Report successfully saved to: {args.output}")
        except Exception as e:
            print(f"Error writing report to file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print to stdout
        if args.format == "json":
            print(format_json_report(result))
        elif args.format == "markdown":
            print(format_markdown_report(result))
        elif args.format == "html":
            fd, temp_path = tempfile.mkstemp(suffix=".html")
            try:
                export_html(result, temp_path)
                with open(temp_path, "r", encoding="utf-8") as f:
                    print(f.read())
            finally:
                os.close(fd)
                os.remove(temp_path)
        elif args.format == "sarif":
            fd, temp_path = tempfile.mkstemp(suffix=".sarif")
            try:
                export_sarif(result, temp_path)
                with open(temp_path, "r", encoding="utf-8") as f:
                    print(f.read())
            finally:
                os.close(fd)
                os.remove(temp_path)
        else:
            print(format_console_report(result))

if __name__ == "__main__":
    main()

