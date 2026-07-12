from codereview.models import ReviewResult, RepositoryReviewResult

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    letter = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    colors = None
    HAS_REPORTLAB = False

def export_pdf(result, filepath: str) -> None:
    """
    Exports the review result to a PDF file.
    Requires 'reportlab' to be installed. If not, raises an ImportError.
    """
    if not HAS_REPORTLAB:
        raise ImportError(
            "PDF generation requires the 'reportlab' package. "
            "Please install it using 'pip install reportlab' to generate PDF reports."
        )

    # Initialize PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    is_repo = isinstance(result, RepositoryReviewResult)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        name="PDFTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        name="PDFH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        name="PDFBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    
    code_style = ParagraphStyle(
        name="PDFCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#E2E8F0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=4
    )

    # Header / Title
    title_text = "Codivus Repository Review Report" if is_repo else "Codivus File Review Report"
    story.append(Paragraph(title_text, title_style))
    story.append(Paragraph(f"Generated on: {result.timestamp or ''}", body_style))
    story.append(Spacer(1, 15))
    
    # Summary Details
    story.append(Paragraph("Quality Metrics Summary", h1_style))
    
    # helper for score formatting
    def format_score_str(score_val: float) -> str:
        if score_val >= 90.0:
            return f"{score_val:.1f}/100 (Excellent)"
        elif score_val >= 70.0:
            return f"{score_val:.1f}/100 (Good)"
        else:
            return f"{score_val:.1f}/100 (Action Required)"

    if is_repo:
        summary = result.summary
        score = result.overall_score
        
        data = [
            ["Metric", "Value", "Score Category", "Score Value"],
            ["Total Files", str(summary.total_files), "Overall Score", format_score_str(score.overall_score)],
            ["Total LOC", str(summary.total_loc), "Security Score", format_score_str(score.security_score)],
            ["Total Issues", str(summary.total_issues), "Performance Score", format_score_str(score.performance_score)],
            ["High/Critical", str(summary.critical_issues + summary.high_issues), "Style/Bug Score", format_score_str(score.style_score)]
        ]
    else:
        summary = result.summary
        score = result.score
        
        data = [
            ["Metric", "Value", "Score Category", "Score Value"],
            ["Total Files", "1", "Overall Score", format_score_str(score.overall_score)],
            ["Total Issues", str(summary.total_issues), "Security Score", format_score_str(score.security_score)],
            ["High/Critical", str(summary.critical_issues + summary.high_issues), "Performance Score", format_score_str(score.performance_score)],
            ["Low/Medium", str(summary.low_issues + summary.medium_issues), "Style Score", format_score_str(score.style_score)]
        ]
        
    t = Table(data, colWidths=[120, 100, 150, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Executive Summary Text
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(summary.summary_text, body_style))
    story.append(Spacer(1, 15))
    
    # Repository Architecture Overview (Repo Only)
    if is_repo and result.architecture_overview:
        story.append(Paragraph("Architecture Overview", h1_style))
        story.append(Paragraph(result.architecture_overview, body_style))
        story.append(Spacer(1, 15))
        
    # Repository level issues
    if is_repo and result.repo_issues:
        story.append(Paragraph("Repository Cross-file Issues", h1_style))
        for issue in result.repo_issues:
            issue_title = f"<b>[{issue.category.upper()} - {issue.severity.upper()}] {issue.title}</b>"
            story.append(Paragraph(issue_title, body_style))
            story.append(Paragraph(issue.description, body_style))
            if issue.suggestion and issue.suggestion.proposed_code:
                story.append(Paragraph(issue.suggestion.proposed_code, code_style))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 10))
        
    # File level issues
    story.append(Paragraph("Detailed Issues Findings List", h1_style))
    
    if is_repo:
        for filepath, f_res in result.file_reviews.items():
            if f_res.issues:
                story.append(Paragraph(f"<b>File: {filepath} ({len(f_res.issues)} issues)</b>", h1_style))
                for issue in f_res.issues:
                    line_str = f"Line {issue.line_number}: " if issue.line_number else ""
                    issue_header = f"• [{issue.category.upper()} - {issue.severity.upper()}] {line_str}<b>{issue.title}</b>"
                    story.append(Paragraph(issue_header, body_style))
                    story.append(Paragraph(issue.description, body_style))
                    
                    if issue.code_snippet:
                        story.append(Paragraph(f"Original: {issue.code_snippet}", code_style))
                    if issue.suggestion and issue.suggestion.proposed_code:
                        story.append(Paragraph(f"Proposed: {issue.suggestion.proposed_code}", code_style))
                    story.append(Spacer(1, 4))
            else:
                story.append(Paragraph(f"<b>File: {filepath} (No issues found)</b>", body_style))
                story.append(Spacer(1, 4))
    else:
        # File issues
        if result.issues:
            for issue in result.issues:
                line_str = f"Line {issue.line_number}: " if issue.line_number else ""
                issue_header = f"• [{issue.category.upper()} - {issue.severity.upper()}] {line_str}<b>{issue.title}</b>"
                story.append(Paragraph(issue_header, body_style))
                story.append(Paragraph(issue.description, body_style))
                
                if issue.code_snippet:
                    story.append(Paragraph(f"Original: {issue.code_snippet}", code_style))
                if issue.suggestion and issue.suggestion.proposed_code:
                    story.append(Paragraph(f"Proposed: {issue.suggestion.proposed_code}", code_style))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("No issues identified in this file.", body_style))
            
    doc.build(story)
