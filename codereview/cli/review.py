import os
import sys
from codereview.reviewer import Reviewer
from codereview.cli.report import format_console_report, format_markdown_report, format_json_report
from codereview.reports import export_json, export_markdown, export_html, export_sarif, export_pdf

def output_result(result, format_type, output_path):
    if format_type == "pdf" and not output_path:
        print("Error: PDF format requires an --output file path.", file=sys.stderr)
        sys.exit(1)

    if output_path:
        try:
            if format_type == "json":
                export_json(result, output_path)
            elif format_type == "markdown":
                export_markdown(result, output_path)
            elif format_type == "html":
                export_html(result, output_path)
            elif format_type == "sarif":
                export_sarif(result, output_path)
            elif format_type == "pdf":
                export_pdf(result, output_path)
            else:
                report_content = format_console_report(result)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report_content)
            print(f"Report successfully saved to: {output_path}")
        except Exception as e:
            print(f"Error writing report to file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        if format_type == "json":
            print(format_json_report(result))
        elif format_type == "markdown":
            print(format_markdown_report(result))
        elif format_type == "html":
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=".html")
            try:
                export_html(result, temp_path)
                with open(temp_path, "r", encoding="utf-8") as f:
                    print(f.read())
            finally:
                os.close(fd)
                os.remove(temp_path)
        elif format_type == "sarif":
            import tempfile
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

def handle_review(args, config):
    reviewer = Reviewer(config)
    
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
        
    output_result(result, args.format, args.output)

def handle_report(args, config):
    import json
    from codereview.models import ReviewResult, RepositoryReviewResult
    
    json_path = os.path.abspath(args.json_file)
    if not os.path.exists(json_path):
        print(f"Error: JSON report file does not exist: {json_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON report: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    try:
        if "file_reviews" in data:
            result = RepositoryReviewResult.model_validate(data)
        else:
            result = ReviewResult.model_validate(data)
    except Exception as e:
        print(f"Error validating review report format: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    output_result(result, args.format, args.output)

