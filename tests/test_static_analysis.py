import pytest
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.models import CodeContext, FileStats
from codereview.parsers.python import PythonParser
from codereview.analyzers.complexity import ComplexityAnalyzer
from codereview.analyzers.deadcode import DeadCodeAnalyzer
from codereview.analyzers.duplication import DuplicationAnalyzer
from codereview.analyzers.metrics import MetricsAnalyzer
from codereview.analyzers import run_static_analysis

def test_complexity_analyzer():
    code = """
def simple():
    return 1

def complex_func(x):
    if x > 1:
        if x > 2:
            if x > 3:
                if x > 4:
                    if x > 5:
                        if x > 6:
                            if x > 7:
                                if x > 8:
                                    if x > 9:
                                        if x > 10:
                                            if x > 11:
                                                if x > 12:
                                                    if x > 13:
                                                        if x > 14:
                                                            if x > 15:
                                                                return x
    return 0
"""
    parser = PythonParser()
    context = parser.parse_code(code, "test_file.py")
    
    analyzer = ComplexityAnalyzer(threshold=10)
    issues = analyzer.analyze(context)
    
    assert len(issues) == 1
    assert issues[0].title == "High Cyclomatic Complexity"
    assert "complex_func" in issues[0].description
    assert issues[0].severity == "high"


def test_dead_code_analyzer():
    code = """
import os
import sys
from typing import List, Dict

def test_fn():
    unused_local = 10
    used_local = 20
    print(used_local)
    return
    print("unreachable!")
"""
    parser = PythonParser()
    context = parser.parse_code(code, "test_file.py")
    
    analyzer = DeadCodeAnalyzer()
    issues = analyzer.analyze(context)
    
    titles = [issue.title for issue in issues]
    assert titles.count("Unused Import") == 4
    assert "Unused Local Variable" in titles
    assert "Unreachable Code" in titles
    
    unused_var_issue = next(i for i in issues if i.title == "Unused Local Variable")
    assert "unused_local" in unused_var_issue.description
    
    unreachable_issue = next(i for i in issues if i.title == "Unreachable Code")
    assert "unreachable!" in unreachable_issue.code_snippet


def test_duplication_analyzer():
    code = """
def func1():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    return x + y + z + a + b

def func2():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    return x + y + z + a + b
"""
    parser = PythonParser()
    context = parser.parse_code(code, "test_file.py")
    
    analyzer = DuplicationAnalyzer(min_lines=5)
    issues = analyzer.analyze(context)
    
    assert len(issues) == 1
    assert issues[0].title == "Duplicate Code Block"
    assert issues[0].line_number > 8


def test_metrics_analyzer():
    # Test low comment density
    code_no_comments = "\n".join([f"x{i} = {i}" for i in range(30)])
    parser = PythonParser()
    context = parser.parse_code(code_no_comments, "test_file.py")
    
    analyzer = MetricsAnalyzer(min_density=0.1, max_functions=2)
    issues = analyzer.analyze(context)
    
    titles = [issue.title for issue in issues]
    assert "Low Comment Density" in titles


def test_score_recalculation():
    reviewer = Reviewer(Config({"openai_api_key": "fake_key"}))
    from codereview.models import Score, Issue
    
    llm_score = Score(
        overall_score=95.0,
        security_score=100.0,
        performance_score=90.0,
        style_score=95.0
    )
    
    static_issues = [
        Issue(title="Static Style Low", description="desc", severity="low", category="style"),
        Issue(title="Static Style Med", description="desc", severity="medium", category="style"),
        Issue(title="Static Sec High", description="desc", severity="high", category="security")
    ]
    
    new_score = reviewer._recalculate_scores(llm_score, static_issues)
    
    assert new_score.overall_score == 65.0
    assert new_score.security_score == 85.0
    assert new_score.performance_score == 90.0
    assert new_score.style_score == 80.0
