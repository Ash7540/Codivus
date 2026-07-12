import html
from codereview.models import ReviewResult, RepositoryReviewResult

def get_score_color(score: float) -> str:
    if score >= 90.0:
        return "#10B981"  # Emerald green
    elif score >= 70.0:
        return "#F59E0B"  # Amber orange
    else:
        return "#EF4444"  # Rose red

def get_severity_color(severity: str) -> str:
    sev = severity.lower()
    if sev == "critical":
        return "#DC2626"
    elif sev == "high":
        return "#EA580C"
    elif sev == "medium":
        return "#CA8A04"
    else:
        return "#2563EB"

def get_category_color(category: str) -> str:
    cat = category.lower()
    if cat == "security":
        return "#7C3AED"  # Violet
    elif cat == "performance":
        return "#0891B2"  # Cyan
    elif cat == "style":
        return "#0D9488"  # Teal
    else:
        return "#4B5563"  # Gray

def format_score_badge(score: float) -> str:
    color = get_score_color(score)
    return f'<span style="background-color: {color}20; color: {color}; border: 1px solid {color}40;" class="score-badge">{score:.1f}/100</span>'

def format_score(score: float) -> str:
    if score >= 90.0:
        return f"{score:.1f}/100 (Excellent)"
    elif score >= 70.0:
        return f"{score:.1f}/100 (Good)"
    else:
        return f"{score:.1f}/100 (Action Required)"

def export_html(result, filepath: str) -> None:
    is_repo = isinstance(result, RepositoryReviewResult)
    
    if is_repo:
        title = "Codivus Repository Review Dashboard"
        summary = result.summary
        score = result.overall_score
        total_files = summary.total_files
        total_loc = summary.total_loc
        total_issues = summary.total_issues
        critical = summary.critical_issues
        high = summary.high_issues
        medium = summary.medium_issues
        low = summary.low_issues
        summary_text = summary.summary_text
        architecture = result.architecture_overview or "No architectural overview generated."
        folder_structure = result.folder_structure
    else:
        title = "Codivus File Review Dashboard"
        summary = result.summary
        score = result.score
        total_files = 1
        total_loc = getattr(result, "stats", None)
        total_loc = total_loc.loc if total_loc else 0
        total_issues = summary.total_issues
        critical = summary.critical_issues
        high = summary.high_issues
        medium = summary.medium_issues
        low = summary.low_issues
        summary_text = summary.summary_text
        architecture = ""
        folder_structure = ""
        
    # Generate Architecture Section
    architecture_html = ""
    if is_repo and result.architecture_overview:
        architecture_html = f"""
        <h2 class="section-title">Architecture Overview</h2>
        <div class="summary-box">
            <p>{html.escape(result.architecture_overview)}</p>
        </div>
        """
        
    # Generate Folder Structure Section
    folder_html = ""
    if is_repo and folder_structure:
        folder_html = f"""
        <h2 class="section-title">Project Layout</h2>
        <div class="folder-tree">{html.escape(folder_structure)}</div>
        """
        
    # Generate Repo Issues
    repo_issues_html = ""
    if is_repo and result.repo_issues:
        repo_issues_html += '<h2 class="section-title">Repository Cross-file Issues</h2>'
        repo_issues_html += '<div style="margin-bottom: 2rem;">'
        for issue in result.repo_issues:
            repo_issues_html += f"""
            <div class="issue-card">
                <div class="issue-meta">
                    <span style="background-color: {get_severity_color(issue.severity)}20; color: {get_severity_color(issue.severity)}; border: 1px solid {get_severity_color(issue.severity)}40;" class="badge">{issue.severity}</span>
                    <span style="background-color: {get_category_color(issue.category)}20; color: {get_category_color(issue.category)}; border: 1px solid {get_category_color(issue.category)}40;" class="badge">{issue.category}</span>
                </div>
                <div class="issue-title">{html.escape(issue.title)}</div>
                <div style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 0.75rem;">{html.escape(issue.description)}</div>
            """
            if issue.suggestion and issue.suggestion.proposed_code:
                repo_issues_html += f"""
                <div class="code-container">
                    <div class="code-label">Suggested Resolution</div>
                    <div class="code-box">{html.escape(issue.suggestion.proposed_code)}</div>
                </div>
                """
            repo_issues_html += "</div>"
        repo_issues_html += "</div>"
        
    # Generate File/Issues list
    file_issues_html = ""
    if is_repo:
        for filepath_item, f_res in result.file_reviews.items():
            issues_content = ""
            if f_res.issues:
                for issue in f_res.issues:
                    line_prefix = f'<span class="badge" style="background-color:#1E293B; color:var(--text-muted);">Line {issue.line_number}</span>' if issue.line_number else ''
                    orig_code_block = ""
                    if issue.code_snippet:
                        orig_code_block = f"""
                        <div class="code-container">
                            <div class="code-label">Original Code snippet</div>
                            <div class="code-box">{html.escape(issue.code_snippet)}</div>
                        </div>
                        """
                    sugg_code_block = ""
                    if issue.suggestion and issue.suggestion.proposed_code:
                        sugg_code_block = f"""
                        <div class="code-container">
                            <div class="code-label">Proposed Code correction</div>
                            <div class="code-box">{html.escape(issue.suggestion.proposed_code)}</div>
                            <div style="font-size: 0.8rem; font-style: italic; color: var(--text-muted); margin-top: 0.25rem;">{html.escape(issue.suggestion.explanation)}</div>
                        </div>
                        """
                    issues_content += f"""
                    <div class="issue-card">
                        <div class="issue-meta">
                            <span style="background-color: {get_severity_color(issue.severity)}20; color: {get_severity_color(issue.severity)}; border: 1px solid {get_severity_color(issue.severity)}40;" class="badge">{issue.severity}</span>
                            <span style="background-color: {get_category_color(issue.category)}20; color: {get_category_color(issue.category)}; border: 1px solid {get_category_color(issue.category)}40;" class="badge">{issue.category}</span>
                            {line_prefix}
                        </div>
                        <div class="issue-title">{html.escape(issue.title)}</div>
                        <div style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 0.75rem;">{html.escape(issue.description)}</div>
                        {orig_code_block}
                        {sugg_code_block}
                    </div>
                    """
            else:
                issues_content = '<div style="color:var(--text-muted); padding: 1rem;">No issues found in this file!</div>'
                
            file_issues_html += f"""
            <div class="file-section">
                <div class="file-header" onclick="toggleFileSection(this)">
                    <div class="file-header-left">
                        <span>📄 {filepath_item}</span>
                        <span class="issue-count-pill">{len(f_res.issues)} issues</span>
                    </div>
                    <div style="display:flex; gap: 0.75rem; align-items:center;">
                        {format_score_badge(f_res.score.overall_score)}
                        <span class="toggle-icon">▶</span>
                    </div>
                </div>
                <div class="file-body">
                    {issues_content}
                </div>
            </div>
            """
    else:
        # Single file review issues
        issues_content = ""
        if result.issues:
            for issue in result.issues:
                line_prefix = f'<span class="badge" style="background-color:#1E293B; color:var(--text-muted);">Line {issue.line_number}</span>' if issue.line_number else ''
                orig_code_block = ""
                if issue.code_snippet:
                    orig_code_block = f"""
                    <div class="code-container">
                        <div class="code-label">Original Code snippet</div>
                        <div class="code-box">{html.escape(issue.code_snippet)}</div>
                    </div>
                    """
                sugg_code_block = ""
                if issue.suggestion and issue.suggestion.proposed_code:
                    sugg_code_block = f"""
                    <div class="code-container">
                        <div class="code-label">Proposed Code correction</div>
                        <div class="code-box">{html.escape(issue.suggestion.proposed_code)}</div>
                        <div style="font-size: 0.8rem; font-style: italic; color: var(--text-muted); margin-top: 0.25rem;">{html.escape(issue.suggestion.explanation)}</div>
                    </div>
                    """
                issues_content += f"""
                <div class="issue-card">
                    <div class="issue-meta">
                        <span style="background-color: {get_severity_color(issue.severity)}20; color: {get_severity_color(issue.severity)}; border: 1px solid {get_severity_color(issue.severity)}40;" class="badge">{issue.severity}</span>
                        <span style="background-color: {get_category_color(issue.category)}20; color: {get_category_color(issue.category)}; border: 1px solid {get_category_color(issue.category)}40;" class="badge">{issue.category}</span>
                        {line_prefix}
                    </div>
                    <div class="issue-title">{html.escape(issue.title)}</div>
                    <div style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 0.75rem;">{html.escape(issue.description)}</div>
                    {orig_code_block}
                    {sugg_code_block}
                </div>
                """
        else:
            issues_content = '<div style="color:var(--text-muted); padding: 1rem;">No issues found in this file!</div>'
            
        file_issues_html = f"""
        <div class="file-section" style="border:none;">
            <div class="file-body" style="display:block; background-color:transparent; border-top:none; padding:0;">
                {issues_content}
            </div>
        </div>
        """
        
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0B0F19;
            --bg-card: #151B2C;
            --bg-border: #222B45;
            --text-main: #F3F4F6;
            --text-muted: #9CA3AF;
            --accent-primary: #3B82F6;
            --accent-success: #10B981;
            --accent-warning: #F59E0B;
            --accent-danger: #EF4444;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--bg-border);
            padding-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(to right, #3B82F6, #10B981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .timestamp {{
            font-size: 0.9rem;
            color: var(--text-muted);
        }}
        
        /* Grid Layouts */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .card {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-border);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
        
        /* Circular Dial Charts */
        .score-dial-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        
        .score-dial {{
            position: relative;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
        }}
        
        .score-dial::before {{
            content: '';
            position: absolute;
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background-color: var(--bg-card);
        }}
        
        .score-value {{
            position: relative;
            font-size: 1.6rem;
            font-weight: 700;
            z-index: 1;
        }}
        
        .score-label {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-main);
        }}
        
        /* Metric Badges */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .kpi-card {{
            text-align: center;
            padding: 1rem;
        }}
        
        .kpi-value {{
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--accent-primary);
        }}
        
        .kpi-label {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Severity Chips */
        .severity-badges {{
            display: flex;
            gap: 0.5rem;
            justify-content: center;
            margin-top: 0.5rem;
        }}
        
        .severity-badge {{
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        /* Sections */
        .section-title {{
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1rem;
            border-left: 4px solid var(--accent-primary);
            padding-left: 0.75rem;
        }}
        
        .summary-box {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        /* Folder Tree Code View */
        .folder-tree {{
            background-color: #080C14;
            border: 1px solid var(--bg-border);
            padding: 1rem;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            overflow-x: auto;
            margin-bottom: 2rem;
            white-space: pre;
        }}
        
        /* Expandable File Sections */
        .file-section {{
            margin-bottom: 1rem;
            border: 1px solid var(--bg-border);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .file-header {{
            background-color: var(--bg-card);
            padding: 1rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            user-select: none;
            transition: background-color 0.2s ease;
        }}
        
        .file-header:hover {{
            background-color: #1E263D;
        }}
        
        .file-header-left {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .issue-count-pill {{
            background-color: #2D3748;
            color: var(--text-main);
            padding: 0.2rem 0.5rem;
            border-radius: 20px;
            font-size: 0.8rem;
        }}
        
        .file-body {{
            display: none;
            padding: 1rem;
            background-color: #0F131E;
            border-top: 1px solid var(--bg-border);
        }}
        
        /* Issues Details styling */
        .issue-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-border);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }}
        
        .issue-meta {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            align-items: center;
        }}
        
        .badge {{
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .issue-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .code-container {{
            margin-top: 0.75rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .code-box {{
            background-color: #0A0D16;
            border: 1px solid #1D2438;
            border-radius: 6px;
            padding: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            white-space: pre;
        }}
        
        .code-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 600;
        }}
        
        .score-badge {{
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{title}</h1>
                <div class="timestamp">Generated on: {result.timestamp or ""}</div>
            </div>
            <div>
                <span class="timestamp" style="font-weight:600;">Codivus v0.1.0</span>
            </div>
        </header>

        <!-- KPI Summary Cards -->
        <div class="kpi-grid">
            <div class="card kpi-card">
                <div class="kpi-value">{total_files}</div>
                <div class="kpi-label">Files Reviewed</div>
            </div>
            <div class="card kpi-card">
                <div class="kpi-value">{total_loc}</div>
                <div class="kpi-label">Lines of Code</div>
            </div>
            <div class="card kpi-card">
                <div class="kpi-value">{total_issues}</div>
                <div class="kpi-label">Issues Found</div>
            </div>
            <div class="card kpi-card">
                <div class="kpi-value" style="color:var(--accent-danger);">{critical + high}</div>
                <div class="kpi-label">High/Critical Issues</div>
            </div>
        </div>

        <!-- Dashboard Score Dials -->
        <div class="dashboard-grid">
            <!-- Overall -->
            <div class="card score-dial-container">
                <div class="score-dial" style="background: conic-gradient({get_score_color(score.overall_score)} {score.overall_score * 3.6}deg, var(--bg-border) 0deg);">
                    <div class="score-value">{score.overall_score:.1f}%</div>
                </div>
                <div class="score-label">Overall Quality</div>
                <div class="severity-badges">
                    <span class="severity-badge" style="background-color: {get_score_color(score.overall_score)}20; color: {get_score_color(score.overall_score)}; border: 1px solid {get_score_color(score.overall_score)}40;">
                        {format_score(score.overall_score).split()[-1]}
                    </span>
                </div>
            </div>
            
            <!-- Security -->
            <div class="card score-dial-container">
                <div class="score-dial" style="background: conic-gradient({get_score_color(score.security_score)} {score.security_score * 3.6}deg, var(--bg-border) 0deg);">
                    <div class="score-value">{score.security_score:.1f}%</div>
                </div>
                <div class="score-label">Security Health</div>
                <div class="severity-badges">
                    <span class="severity-badge" style="background-color: {get_score_color(score.security_score)}20; color: {get_score_color(score.security_score)}; border: 1px solid {get_score_color(score.security_score)}40;">
                        {format_score(score.security_score).split()[-1]}
                    </span>
                </div>
            </div>
            
            <!-- Performance -->
            <div class="card score-dial-container">
                <div class="score-dial" style="background: conic-gradient({get_score_color(score.performance_score)} {score.performance_score * 3.6}deg, var(--bg-border) 0deg);">
                    <div class="score-value">{score.performance_score:.1f}%</div>
                </div>
                <div class="score-label">Performance Health</div>
                <div class="severity-badges">
                    <span class="severity-badge" style="background-color: {get_score_color(score.performance_score)}20; color: {get_score_color(score.performance_score)}; border: 1px solid {get_score_color(score.performance_score)}40;">
                        {format_score(score.performance_score).split()[-1]}
                    </span>
                </div>
            </div>
            
            <!-- Style -->
            <div class="card score-dial-container">
                <div class="score-dial" style="background: conic-gradient({get_score_color(score.style_score)} {score.style_score * 3.6}deg, var(--bg-border) 0deg);">
                    <div class="score-value">{score.style_score:.1f}%</div>
                </div>
                <div class="score-label">Style & Standards</div>
                <div class="severity-badges">
                    <span class="severity-badge" style="background-color: {get_score_color(score.style_score)}20; color: {get_score_color(score.style_score)}; border: 1px solid {get_score_color(score.style_score)}40;">
                        {format_score(score.style_score).split()[-1]}
                    </span>
                </div>
            </div>
        </div>

        <!-- Executive Summary -->
        <h2 class="section-title">Executive Summary</h2>
        <div class="summary-box">
            <p>{summary_text}</p>
        </div>

        <!-- Architecture Overview -->
        {architecture_html}

        <!-- Folder Structure -->
        {folder_html}

        <!-- Repository level issues -->
        {repo_issues_html}

        <!-- File issues expandable -->
        <h2 class="section-title">File Details & Issues</h2>
        <div style="margin-bottom: 2rem;">
            {file_issues_html}
        </div>
    </div>

    <script>
        function toggleFileSection(header) {{
            const body = header.nextElementSibling;
            const icon = header.querySelector('.toggle-icon');
            if (body.style.display === 'block') {{
                body.style.display = 'none';
                icon.textContent = '▶';
                icon.style.transform = 'rotate(0deg)';
            }} else {{
                body.style.display = 'block';
                icon.textContent = '▼';
            }}
        }}
    </script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
