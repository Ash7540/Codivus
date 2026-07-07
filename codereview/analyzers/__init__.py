from typing import List
from codereview.models import Issue, CodeContext
from codereview.analyzers.base import BaseAnalyzer
from codereview.analyzers.complexity import ComplexityAnalyzer
from codereview.analyzers.deadcode import DeadCodeAnalyzer
from codereview.analyzers.duplication import DuplicationAnalyzer
from codereview.analyzers.metrics import MetricsAnalyzer
from codereview.security import SecurityAnalyzer
from codereview.performance import PerformanceAnalyzer

def run_static_analysis(context: CodeContext) -> List[Issue]:
    """
    Executes all static analyzers on the provided CodeContext and returns aggregated issues.
    """
    analyzers: List[BaseAnalyzer] = [
        ComplexityAnalyzer(),
        DeadCodeAnalyzer(),
        DuplicationAnalyzer(),
        MetricsAnalyzer(),
        SecurityAnalyzer(),
        PerformanceAnalyzer(),
    ]
    
    all_issues = []
    for analyzer in analyzers:
        try:
            issues = analyzer.analyze(context)
            all_issues.extend(issues)
        except Exception as e:
            import sys
            print(f"Error in analyzer {analyzer.__class__.__name__}: {str(e)}", file=sys.stderr)
            
    return all_issues

__all__ = [
    "BaseAnalyzer",
    "ComplexityAnalyzer",
    "DeadCodeAnalyzer",
    "DuplicationAnalyzer",
    "MetricsAnalyzer",
    "SecurityAnalyzer",
    "PerformanceAnalyzer",
    "run_static_analysis",
]


