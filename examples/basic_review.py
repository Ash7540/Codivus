import os
import sys
from dotenv import load_dotenv
from codereview.config import Config
from codereview.reviewer import Reviewer

def main():
    # Load .env file variables
    load_dotenv()

    # 1. Create a dummy Python file to review
    dummy_code = """
def calculate_area(radius):
    # Bug: using string representation of pi
    pi = "3.14159"
    return pi * radius * radius

def greet_user(name):
    # Style: unused variable and print statement without f-string
    msg = "Hello " + name
    unused_var = 42
    print("Greeting has been sent")
    return msg
"""
    
    temp_file = "temp_dummy_code.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(dummy_code.strip())
        
    print(f"Created temporary dummy file '{temp_file}' for review.")

    # 2. Check for OpenAI key, if missing use mock provider for testing
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAPI_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found. Using 'mock' provider for demonstration.")
        config = Config({
            "default_provider": "mock"
        })
    else:
        print("OPENAI_API_KEY found. Running live review using OpenAI...")
        config = Config() # Uses default config loading standard keys

    try:
        # 3. Instantiate reviewer and run review
        reviewer = Reviewer(config)
        print(f"Running review on '{temp_file}'...")
        result = reviewer.review_file(temp_file)
        
        # 4. Print results
        print("\n=== Review Results ===")
        print(f"Timestamp: {result.timestamp}")
        print(f"Executive Summary: {result.summary.summary_text}")
        print(f"Total Issues Found: {result.summary.total_issues}")
        
        print("\n--- Scores ---")
        print(f"Overall:     {result.score.overall_score}/100")
        print(f"Security:    {result.score.security_score}/100")
        print(f"Performance: {result.score.performance_score}/100")
        print(f"Style:       {result.score.style_score}/100")
        
        print("\n--- Issues ---")
        for i, issue in enumerate(result.issues, start=1):
            print(f"\nIssue #{i}: {issue.title}")
            print(f"  Category: {issue.category} | Severity: {issue.severity}")
            if issue.line_number is not None:
                print(f"  Line: {issue.line_number}")
            print(f"  Description: {issue.description}")
            if issue.suggestion:
                print(f"  Suggestion:")
                print(f"    Original: {issue.suggestion.original_code}")
                print(f"    Proposed: {issue.suggestion.proposed_code}")
                print(f"    Explanation: {issue.suggestion.explanation}")

    except Exception as e:
        print(f"Review failed: {e}", file=sys.stderr)
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\nTemporary file '{temp_file}' cleaned up.")

if __name__ == "__main__":
    main()
