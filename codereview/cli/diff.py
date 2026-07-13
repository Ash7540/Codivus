import os
import sys
from codereview.reviewer import Reviewer
from codereview.cli.review import output_result

def handle_diff(args, config):
    reviewer = Reviewer(config)
    ref_range = args.ref_range
    repo_path = args.path
    
    try:
        result = reviewer.review_diff(ref_range, repo_path)
    except Exception as e:
        print(f"Error executing diff review: {str(e)}", file=sys.stderr)
        sys.exit(1)
        
    output_result(result, args.format, args.output)
