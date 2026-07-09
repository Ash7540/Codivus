import os
import pytest
from codereview.config import Config
from codereview.reviewer import Reviewer
from codereview.models import RepositoryReviewResult, Issue

def test_repository_review_flow(tmp_path):
    # Create a mock repository structure:
    # my_project/
    # ├── a.py (imports b)
    # ├── b.py (imports a - circular!)
    # └── sub/
    #     ├── __init__.py
    #     └── c.py (imports sub.non_existent - broken!)
    
    project_dir = tmp_path / "my_project"
    project_dir.mkdir()
    
    a_file = project_dir / "a.py"
    a_file.write_text('"""Module A."""\nimport b\n', encoding="utf-8")
    
    b_file = project_dir / "b.py"
    b_file.write_text('"""Module B."""\nimport a\n', encoding="utf-8")
    
    sub_dir = project_dir / "sub"
    sub_dir.mkdir()
    
    sub_init = sub_dir / "__init__.py"
    sub_init.write_text('"""Sub package."""\n', encoding="utf-8")
    
    c_file = sub_dir / "c.py"
    c_file.write_text('"""Module C."""\nimport b\nimport sub.non_existent\n', encoding="utf-8")
    
    # Initialize Reviewer with Mock Provider
    config = Config({"default_provider": "mock", "openai_api_key": "fake"})
    reviewer = Reviewer(config)
    
    # Run directory review
    result = reviewer.review_dir(str(project_dir))
    
    assert isinstance(result, RepositoryReviewResult)
    
    # Verify file scanning
    assert result.summary.total_files == 4  # a.py, b.py, sub/__init__.py, sub/c.py
    
    # Verify folder structure is populated
    assert "my_project/" in result.folder_structure
    assert "sub/" in result.folder_structure
    
    # Verify circular dependency detection
    # Graph has a.py -> b.py and b.py -> a.py
    cycle_issues = [i for i in result.repo_issues if i.title == "Circular Dependency Detected"]
    assert len(cycle_issues) >= 1
    assert any("a.py -> b.py -> a.py" in i.description or "b.py -> a.py -> b.py" in i.description for i in cycle_issues)
    
    # Verify broken local import detection
    # sub/c.py imports sub.non_existent
    broken_issues = [i for i in result.repo_issues if i.title == "Broken Local Import"]
    assert len(broken_issues) == 1
    assert "sub.non_existent" in broken_issues[0].description
    assert broken_issues[0].severity == "high"
    assert broken_issues[0].category == "bug"
    
    # Verify individual file reviews are collected
    assert "a.py" in result.file_reviews
    assert "b.py" in result.file_reviews
    assert "sub/c.py" in result.file_reviews
    
    # Assert score recalculation handles repo issues
    # Mock files return score 85.0.
    # Unused imports in a.py (5), b.py (5), sub/c.py (10) decrease file average to 80.0.
    # Repository issues include 1 high (15 points) and 1 medium (10 points) -> total 25 points deduction
    # 80.0 - 25.0 = 55.0 overall score
    assert result.overall_score.overall_score == 55.0
