import os
import json
import pytest
from unittest.mock import patch, MagicMock
from codereview.models import ReviewResult, Summary, Score, RepositoryReviewResult, RepositorySummary, Issue, Suggestion
from codereview.reports.json import export_json
from codereview.reports.markdown import export_markdown
from codereview.reports.html import export_html
from codereview.reports.sarif import export_sarif
from codereview.reports.pdf import export_pdf

@pytest.fixture
def dummy_result():
    return ReviewResult(
        summary=Summary(
            total_issues=1,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=1,
            summary_text="Mock file review summary."
        ),
        score=Score(
            overall_score=85.0,
            security_score=100.0,
            performance_score=90.0,
            style_score=65.0
        ),
        issues=[
            Issue(
                title="Mock Style Violation",
                description="Docstrings are missing.",
                severity="low",
                category="style",
                line_number=2,
                code_snippet="def f():",
                suggestion=Suggestion(
                    original_code="def f():",
                    proposed_code='def f():\n    """Docstring."""',
                    explanation="PEP 257 check."
                )
            )
        ],
        timestamp="2026-07-12T12:00:00Z"
    )

@pytest.fixture
def dummy_repo_result(dummy_result):
    return RepositoryReviewResult(
        summary=RepositorySummary(
            total_files=1,
            total_loc=10,
            total_issues=1,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=1,
            summary_text="Mock repository review summary."
        ),
        overall_score=Score(
            overall_score=85.0,
            security_score=100.0,
            performance_score=90.0,
            style_score=65.0
        ),
        file_reviews={"a.py": dummy_result},
        repo_issues=[
            Issue(
                title="Circular Dependency Detected",
                description="a.py -> b.py -> a.py",
                severity="medium",
                category="style",
                line_number=None,
                code_snippet=None,
                suggestion=None
            )
        ],
        architecture_overview="Mock repo architecture overview.",
        folder_structure="my_project/\n└── a.py",
        timestamp="2026-07-12T12:00:00Z"
    )

def test_json_exporter(dummy_repo_result, tmp_path):
    out_file = tmp_path / "report.json"
    export_json(dummy_repo_result, str(out_file))
    
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["summary"]["total_files"] == 1
    assert data["overall_score"]["overall_score"] == 85.0

def test_markdown_exporter(dummy_repo_result, tmp_path):
    out_file = tmp_path / "report.md"
    export_markdown(dummy_repo_result, str(out_file))
    
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "# Codivus Code Review Report" in content
    assert "## Repository Summary" in content

def test_html_exporter(dummy_repo_result, tmp_path):
    out_file = tmp_path / "report.html"
    export_html(dummy_repo_result, str(out_file))
    
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Codivus Repository Review Dashboard" in content
    assert "conic-gradient" in content
    assert "my_project/" in content

def test_sarif_exporter(dummy_repo_result, tmp_path):
    out_file = tmp_path / "report.sarif"
    export_sarif(dummy_repo_result, str(out_file))
    
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    
    # Check SARIF Schema properties
    assert data["version"] == "2.1.0"
    assert "$schema" in data
    assert len(data["runs"]) == 1
    run = data["runs"][0]
    assert run["tool"]["driver"]["name"] == "Codivus"
    
    # Ensure circular dependency and file issue are represented in results
    results = run["results"]
    assert len(results) == 2
    assert any(r["ruleId"] == "COD-STYLE" and r["level"] == "warning" for r in results) # Circular dependency (medium)
    assert any(r["ruleId"] == "COD-STYLE" and r["level"] == "note" for r in results) # Missing docstring (low)

def test_pdf_exporter_fallback(dummy_repo_result, tmp_path):
    out_file = tmp_path / "report.pdf"
    
    with patch("codereview.reports.pdf.HAS_REPORTLAB", False):
        with pytest.raises(ImportError) as exc:
            export_pdf(dummy_repo_result, str(out_file))
        assert "PDF generation requires the 'reportlab' package" in str(exc.value)

@patch("codereview.reports.pdf.SimpleDocTemplate")
@patch("codereview.reports.pdf.Paragraph")
@patch("codereview.reports.pdf.Spacer")
@patch("codereview.reports.pdf.Table")
@patch("codereview.reports.pdf.TableStyle")
@patch("codereview.reports.pdf.getSampleStyleSheet")
@patch("codereview.reports.pdf.ParagraphStyle")
@patch("codereview.reports.pdf.colors")
@patch("codereview.reports.pdf.letter")
def test_pdf_exporter_build(
    mock_letter, mock_colors, mock_ps, mock_gss, mock_ts, mock_t, mock_s, mock_p, mock_doc,
    dummy_repo_result, tmp_path
):
    out_file = tmp_path / "report.pdf"
    
    # Mock return value for getSampleStyleSheet
    mock_styles = MagicMock()
    mock_styles.__getitem__.return_value = MagicMock()
    mock_gss.return_value = mock_styles
    
    with patch("codereview.reports.pdf.HAS_REPORTLAB", True):
        export_pdf(dummy_repo_result, str(out_file))
        mock_doc.assert_called_once()

