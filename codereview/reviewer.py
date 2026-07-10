import os
from datetime import datetime
from typing import Optional, List, Dict, Set
from codereview.config import Config
from codereview.llm.router import get_provider
from codereview.models import (
    ReviewResult,
    Summary,
    Score,
    RepositorySummary,
    RepositoryReviewResult,
    Issue,
    Suggestion,
)
from codereview.parsers import get_parser_for_file
from codereview.analyzers import run_static_analysis

class Reviewer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.provider = get_provider(self.config.default_provider, self.config)

    def review_file(self, filepath: str, modified_lines: Optional[Set[int]] = None) -> ReviewResult:
        """
        Reviews a single file and returns structured review results.
        If modified_lines is specified, only issues on those lines are returned.
        """
        abs_filepath = os.path.abspath(filepath)
        
        if not os.path.exists(abs_filepath):
            raise FileNotFoundError(f"File not found: {abs_filepath}")
        
        if not os.path.isfile(abs_filepath):
            raise ValueError(f"Path is not a file: {abs_filepath}")
            
        try:
            with open(abs_filepath, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {abs_filepath}: {str(e)}")

        # 1. Parse file content into CodeContext
        parser = get_parser_for_file(abs_filepath)
        code_context = parser.parse_code(code_content, abs_filepath)

        # 2. Run deterministic static analysis
        static_issues = run_static_analysis(code_context)

        # 3. Invoke LLM provider with CodeContext and static analysis findings
        llm_result = self.provider.generate_review(code_context, static_issues, modified_lines)

        # 4. Merge static analysis issues with LLM issues
        combined_issues = static_issues + llm_result.issues

        # Filter issues if modified_lines is provided
        if modified_lines is not None:
            combined_issues = [
                i for i in combined_issues 
                if i.line_number is None or i.line_number in modified_lines
            ]
            # Also filter static issues for local scoring recalculations
            static_issues = [
                i for i in static_issues 
                if i.line_number is None or i.line_number in modified_lines
            ]

        # 5. Recalculate summary metrics based on the combined list
        total_issues = len(combined_issues)
        critical_count = sum(1 for i in combined_issues if i.severity.lower() == "critical")
        high_count = sum(1 for i in combined_issues if i.severity.lower() == "high")
        medium_count = sum(1 for i in combined_issues if i.severity.lower() == "medium")
        low_count = sum(1 for i in combined_issues if i.severity.lower() == "low")

        summary_text = llm_result.summary.summary_text
        if static_issues:
            summary_text += f" Static analysis discovered {len(static_issues)} additional issues."

        new_summary = Summary(
            total_issues=total_issues,
            critical_issues=critical_count,
            high_issues=high_count,
            medium_issues=medium_count,
            low_issues=low_count,
            summary_text=summary_text
        )

        # 6. Recalculate quality scores with static analysis deductions
        new_score = self._recalculate_scores(llm_result.score, static_issues)

        # 7. Construct final ReviewResult
        return ReviewResult(
            summary=new_summary,
            score=new_score,
            issues=combined_issues,
            timestamp=llm_result.timestamp
        )

    def review_dir(self, dirpath: str) -> RepositoryReviewResult:
        """
        Reviews a directory containing a Python project codebase and returns RepositoryReviewResult.
        """
        abs_dirpath = os.path.abspath(dirpath)
        if not os.path.exists(abs_dirpath):
            raise FileNotFoundError(f"Directory not found: {abs_dirpath}")
        if not os.path.isdir(abs_dirpath):
            raise ValueError(f"Path is not a directory: {abs_dirpath}")

        EXCLUDES = {
            ".git", "__pycache__", ".venv", "env", "venv", ".pytest_cache", ".agents",
            "build", "dist", ".github", "egg-info", "codivus.egg-info", ".idea", ".vscode"
        }

        # 1. Recursive scan of python files
        all_py_files = []
        for root, dirs, files in os.walk(abs_dirpath):
            dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('.')]
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, abs_dirpath).replace('\\', '/')
                    all_py_files.append((full_path, rel_path))

        # Sort files for deterministic execution order
        all_py_files.sort(key=lambda x: x[1])

        # 2. Run file-level reviews
        file_reviews = {}
        total_loc = 0
        all_static_issues = []
        file_summaries = []
        dep_graph = {}
        all_rel_files = {rel_path for _, rel_path in all_py_files}

        for full_path, rel_path in all_py_files:
            review_res = self.review_file(full_path)
            file_reviews[rel_path] = review_res
            
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            parser = get_parser_for_file(full_path)
            context = parser.parse_code(content, full_path)
            total_loc += context.stats.loc
            
            # Map internal dependencies
            deps = []
            for imp in context.imports:
                resolved = self._resolve_import_to_local_file(imp.name, abs_dirpath, full_path)
                if resolved and resolved in all_rel_files:
                    deps.append(resolved)
            dep_graph[rel_path] = deps
            
            # Check for broken local imports in this file
            broken_imports = self._check_broken_local_imports(context.imports, abs_dirpath, rel_path, all_rel_files)
            all_static_issues.extend(broken_imports)
            
            file_summaries.append(f"- File `{rel_path}`: {review_res.summary.summary_text}")

        # 3. Detect circular dependencies
        cycles = self._find_circular_dependencies(dep_graph)
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            all_static_issues.append(Issue(
                title="Circular Dependency Detected",
                description=f"A circular dependency chain was detected: {cycle_str}. Circular dependencies tightly couple modules and make them harder to read and maintain.",
                severity="medium",
                category="style",
                line_number=None,
                code_snippet=None,
                suggestion=Suggestion(
                    original_code="",
                    proposed_code="# Refactor modules to break dependency cycle, e.g. using interfaces or a third shared module.",
                    explanation="Breaking circular imports decreases coupling and simplifies testing and extension."
                )
            ))

        # 4. Generate folder structure tree
        folder_structure = self._generate_folder_tree(abs_dirpath, EXCLUDES)

        # 5. Invoke LLM for repository overview
        llm_repo_res = self.provider.generate_repo_summary(
            folder_structure=folder_structure,
            dependency_map=dep_graph,
            repo_issues=all_static_issues,
            file_summaries=file_summaries
        )

        # 6. Compute overall metrics
        all_combined_issues = all_static_issues.copy()
        for f_res in file_reviews.values():
            all_combined_issues.extend(f_res.issues)
            
        total_issues = len(all_combined_issues)
        critical_count = sum(1 for i in all_combined_issues if i.severity.lower() == "critical")
        high_count = sum(1 for i in all_combined_issues if i.severity.lower() == "high")
        medium_count = sum(1 for i in all_combined_issues if i.severity.lower() == "medium")
        low_count = sum(1 for i in all_combined_issues if i.severity.lower() == "low")

        repo_summary = RepositorySummary(
            total_files=len(all_py_files),
            total_loc=total_loc,
            total_issues=total_issues,
            critical_issues=critical_count,
            high_issues=high_count,
            medium_issues=medium_count,
            low_issues=low_count,
            summary_text=llm_repo_res["summary_text"]
        )

        # 7. Compute overall scores
        avg_overall = sum(r.score.overall_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_security = sum(r.score.security_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_performance = sum(r.score.performance_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_style = sum(r.score.style_score for r in file_reviews.values()) / max(1, len(file_reviews))

        severity_deductions = {
            "critical": 20.0,
            "high": 15.0,
            "medium": 10.0,
            "low": 5.0
        }
        for issue in all_static_issues:
            deduction = severity_deductions.get(issue.severity.lower(), 5.0)
            avg_overall -= deduction
            
            cat = issue.category.lower()
            if cat == "security":
                avg_security -= deduction
            elif cat == "performance":
                avg_performance -= deduction
            elif cat == "style" or cat == "bug":
                avg_style -= deduction

        final_score = Score(
            overall_score=max(0.0, min(100.0, avg_overall)),
            security_score=max(0.0, min(100.0, avg_security)),
            performance_score=max(0.0, min(100.0, avg_performance)),
            style_score=max(0.0, min(100.0, avg_style))
        )

        return RepositoryReviewResult(
            summary=repo_summary,
            overall_score=final_score,
            file_reviews=file_reviews,
            repo_issues=all_static_issues,
            architecture_overview=llm_repo_res["architecture_overview"],
            folder_structure=folder_structure,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    def review_staged(self, repo_path: str = ".") -> RepositoryReviewResult:
        """
        Reviews only the staged files in a git repository, targeting only the modified lines.
        """
        from codereview.git import GitRepository, parse_diff_added_lines

        repo = GitRepository(repo_path)
        if not repo.is_git_repo():
            raise RuntimeError(f"Path is not a git repository: {repo_path}")

        staged_files = repo.get_staged_files()
        if not staged_files:
            return RepositoryReviewResult(
                summary=RepositorySummary(
                    total_files=0,
                    total_loc=0,
                    total_issues=0,
                    critical_issues=0,
                    high_issues=0,
                    medium_issues=0,
                    low_issues=0,
                    summary_text="No staged Python files found to review."
                ),
                overall_score=Score(overall_score=100.0, security_score=100.0, performance_score=100.0, style_score=100.0),
                file_reviews={},
                repo_issues=[],
                architecture_overview="No staged changes reviewed.",
                folder_structure="",
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        file_reviews = {}
        total_loc = 0
        all_static_issues = []
        file_summaries = []
        dep_graph = {}
        all_rel_files = {os.path.relpath(f, repo.repo_path).replace('\\', '/') for f in staged_files}

        for full_path in staged_files:
            rel_path = os.path.relpath(full_path, repo.repo_path).replace('\\', '/')
            diff_text = repo.get_staged_diff(full_path)
            modified_lines = parse_diff_added_lines(diff_text)

            review_res = self.review_file(full_path, modified_lines)
            file_reviews[rel_path] = review_res

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            parser = get_parser_for_file(full_path)
            context = parser.parse_code(content, full_path)
            total_loc += context.stats.loc

            deps = []
            for imp in context.imports:
                resolved = self._resolve_import_to_local_file(imp.name, repo.repo_path, full_path)
                if resolved and resolved in all_rel_files:
                    deps.append(resolved)
            dep_graph[rel_path] = deps

            broken_imports = self._check_broken_local_imports(context.imports, repo.repo_path, rel_path, all_rel_files)
            broken_imports = [i for i in broken_imports if i.line_number is None or i.line_number in modified_lines]
            all_static_issues.extend(broken_imports)

            file_summaries.append(f"- File `{rel_path}` (staged): {review_res.summary.summary_text}")

        cycles = self._find_circular_dependencies(dep_graph)
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            all_static_issues.append(Issue(
                title="Circular Dependency Detected",
                description=f"A circular dependency chain was detected: {cycle_str} in staged changes.",
                severity="medium",
                category="style",
                line_number=None,
                code_snippet=None,
                suggestion=Suggestion(
                    original_code="",
                    proposed_code="# Refactor modules to break dependency cycle.",
                    explanation="Breaking circular imports decreases coupling and simplifies testing and extension."
                )
            ))

        folder_structure = self._generate_folder_tree(repo.repo_path, {".git", "__pycache__", ".venv", "env", "venv", ".pytest_cache", ".agents"})

        llm_repo_res = self.provider.generate_repo_summary(
            folder_structure=folder_structure,
            dependency_map=dep_graph,
            repo_issues=all_static_issues,
            file_summaries=file_summaries
        )

        all_combined_issues = all_static_issues.copy()
        for f_res in file_reviews.values():
            all_combined_issues.extend(f_res.issues)

        total_issues = len(all_combined_issues)
        critical_count = sum(1 for i in all_combined_issues if i.severity.lower() == "critical")
        high_count = sum(1 for i in all_combined_issues if i.severity.lower() == "high")
        medium_count = sum(1 for i in all_combined_issues if i.severity.lower() == "medium")
        low_count = sum(1 for i in all_combined_issues if i.severity.lower() == "low")

        repo_summary = RepositorySummary(
            total_files=len(staged_files),
            total_loc=total_loc,
            total_issues=total_issues,
            critical_issues=critical_count,
            high_issues=high_count,
            medium_issues=medium_count,
            low_issues=low_count,
            summary_text=llm_repo_res["summary_text"]
        )

        avg_overall = sum(r.score.overall_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_security = sum(r.score.security_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_performance = sum(r.score.performance_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_style = sum(r.score.style_score for r in file_reviews.values()) / max(1, len(file_reviews))

        severity_deductions = {
            "critical": 20.0,
            "high": 15.0,
            "medium": 10.0,
            "low": 5.0
        }
        for issue in all_static_issues:
            deduction = severity_deductions.get(issue.severity.lower(), 5.0)
            avg_overall -= deduction
            cat = issue.category.lower()
            if cat == "security":
                avg_security -= deduction
            elif cat == "performance":
                avg_performance -= deduction
            elif cat == "style" or cat == "bug":
                avg_style -= deduction

        final_score = Score(
            overall_score=max(0.0, min(100.0, avg_overall)),
            security_score=max(0.0, min(100.0, avg_security)),
            performance_score=max(0.0, min(100.0, avg_performance)),
            style_score=max(0.0, min(100.0, avg_style))
        )

        return RepositoryReviewResult(
            summary=repo_summary,
            overall_score=final_score,
            file_reviews=file_reviews,
            repo_issues=all_static_issues,
            architecture_overview=llm_repo_res["architecture_overview"],
            folder_structure=folder_structure,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    def review_commit(self, commit_hash: str, repo_path: str = ".") -> RepositoryReviewResult:
        """
        Reviews only the changes introduced in a specific git commit.
        """
        from codereview.git import GitRepository, parse_diff_added_lines

        repo = GitRepository(repo_path)
        if not repo.is_git_repo():
            raise RuntimeError(f"Path is not a git repository: {repo_path}")

        commit_files = repo.get_files_in_commit(commit_hash)
        if not commit_files:
            return RepositoryReviewResult(
                summary=RepositorySummary(
                    total_files=0,
                    total_loc=0,
                    total_issues=0,
                    critical_issues=0,
                    high_issues=0,
                    medium_issues=0,
                    low_issues=0,
                    summary_text=f"No Python files found in commit {commit_hash}."
                ),
                overall_score=Score(overall_score=100.0, security_score=100.0, performance_score=100.0, style_score=100.0),
                file_reviews={},
                repo_issues=[],
                architecture_overview=f"No changes reviewed for commit {commit_hash}.",
                folder_structure="",
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        file_reviews = {}
        total_loc = 0
        all_static_issues = []
        file_summaries = []
        dep_graph = {}
        all_rel_files = {os.path.relpath(f, repo.repo_path).replace('\\', '/') for f in commit_files}

        for full_path in commit_files:
            rel_path = os.path.relpath(full_path, repo.repo_path).replace('\\', '/')
            diff_text = repo.get_commit_diff(commit_hash, full_path)
            modified_lines = parse_diff_added_lines(diff_text)

            review_res = self.review_file(full_path, modified_lines)
            file_reviews[rel_path] = review_res

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            parser = get_parser_for_file(full_path)
            context = parser.parse_code(content, full_path)
            total_loc += context.stats.loc

            deps = []
            for imp in context.imports:
                resolved = self._resolve_import_to_local_file(imp.name, repo.repo_path, full_path)
                if resolved and resolved in all_rel_files:
                    deps.append(resolved)
            dep_graph[rel_path] = deps

            broken_imports = self._check_broken_local_imports(context.imports, repo.repo_path, rel_path, all_rel_files)
            broken_imports = [i for i in broken_imports if i.line_number is None or i.line_number in modified_lines]
            all_static_issues.extend(broken_imports)

            file_summaries.append(f"- File `{rel_path}` (commit {commit_hash}): {review_res.summary.summary_text}")

        cycles = self._find_circular_dependencies(dep_graph)
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            all_static_issues.append(Issue(
                title="Circular Dependency Detected",
                description=f"A circular dependency chain was detected: {cycle_str} in commit {commit_hash}.",
                severity="medium",
                category="style",
                line_number=None,
                code_snippet=None,
                suggestion=Suggestion(
                    original_code="",
                    proposed_code="# Refactor modules to break dependency cycle.",
                    explanation="Breaking circular imports decreases coupling and simplifies testing and extension."
                )
            ))

        folder_structure = self._generate_folder_tree(repo.repo_path, {".git", "__pycache__", ".venv", "env", "venv", ".pytest_cache", ".agents"})

        llm_repo_res = self.provider.generate_repo_summary(
            folder_structure=folder_structure,
            dependency_map=dep_graph,
            repo_issues=all_static_issues,
            file_summaries=file_summaries
        )

        all_combined_issues = all_static_issues.copy()
        for f_res in file_reviews.values():
            all_combined_issues.extend(f_res.issues)

        total_issues = len(all_combined_issues)
        critical_count = sum(1 for i in all_combined_issues if i.severity.lower() == "critical")
        high_count = sum(1 for i in all_combined_issues if i.severity.lower() == "high")
        medium_count = sum(1 for i in all_combined_issues if i.severity.lower() == "medium")
        low_count = sum(1 for i in all_combined_issues if i.severity.lower() == "low")

        repo_summary = RepositorySummary(
            total_files=len(commit_files),
            total_loc=total_loc,
            total_issues=total_issues,
            critical_issues=critical_count,
            high_issues=high_count,
            medium_issues=medium_count,
            low_issues=low_count,
            summary_text=llm_repo_res["summary_text"]
        )

        avg_overall = sum(r.score.overall_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_security = sum(r.score.security_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_performance = sum(r.score.performance_score for r in file_reviews.values()) / max(1, len(file_reviews))
        avg_style = sum(r.score.style_score for r in file_reviews.values()) / max(1, len(file_reviews))

        severity_deductions = {
            "critical": 20.0,
            "high": 15.0,
            "medium": 10.0,
            "low": 5.0
        }
        for issue in all_static_issues:
            deduction = severity_deductions.get(issue.severity.lower(), 5.0)
            avg_overall -= deduction
            cat = issue.category.lower()
            if cat == "security":
                avg_security -= deduction
            elif cat == "performance":
                avg_performance -= deduction
            elif cat == "style" or cat == "bug":
                avg_style -= deduction

        final_score = Score(
            overall_score=max(0.0, min(100.0, avg_overall)),
            security_score=max(0.0, min(100.0, avg_security)),
            performance_score=max(0.0, min(100.0, avg_performance)),
            style_score=max(0.0, min(100.0, avg_style))
        )

        return RepositoryReviewResult(
            summary=repo_summary,
            overall_score=final_score,
            file_reviews=file_reviews,
            repo_issues=all_static_issues,
            architecture_overview=llm_repo_res["architecture_overview"],
            folder_structure=folder_structure,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    def _recalculate_scores(self, llm_score: Score, static_issues) -> Score:
        overall = llm_score.overall_score
        security = llm_score.security_score
        performance = llm_score.performance_score
        style = llm_score.style_score

        severity_deductions = {
            "critical": 20.0,
            "high": 15.0,
            "medium": 10.0,
            "low": 5.0
        }

        for issue in static_issues:
            deduction = severity_deductions.get(issue.severity.lower(), 5.0)
            overall -= deduction
            
            cat = issue.category.lower()
            if cat == "security":
                security -= deduction
            elif cat == "performance":
                performance -= deduction
            elif cat == "style" or cat == "bug":
                style -= deduction

        return Score(
            overall_score=max(0.0, min(100.0, overall)),
            security_score=max(0.0, min(100.0, security)),
            performance_score=max(0.0, min(100.0, performance)),
            style_score=max(0.0, min(100.0, style))
        )

    def _generate_folder_tree(self, dirpath: str, excludes: Set[str]) -> str:
        tree_lines = []
        base_name = os.path.basename(os.path.abspath(dirpath))
        tree_lines.append(f"{base_name}/")
        
        def walk_tree(current_dir, prefix=""):
            try:
                entries = sorted(os.listdir(current_dir))
            except Exception:
                return
                
            entries = [e for e in entries if e not in excludes and not e.startswith('.')]
            
            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                full_path = os.path.join(current_dir, entry)
                
                if os.path.isdir(full_path):
                    tree_lines.append(f"{prefix}{connector}{entry}/")
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    walk_tree(full_path, new_prefix)
                else:
                    tree_lines.append(f"{prefix}{connector}{entry}")
                    
        walk_tree(os.path.abspath(dirpath))
        return "\n".join(tree_lines)

    def _resolve_import_to_local_file(self, import_name: str, root_dir: str, current_file: str) -> Optional[str]:
        parts = import_name.split('.')
        # 1. Absolute import from root
        possible_path = os.path.join(root_dir, *parts) + ".py"
        if os.path.exists(possible_path):
            return os.path.relpath(possible_path, root_dir).replace('\\', '/')
            
        possible_dir = os.path.join(root_dir, *parts, "__init__.py")
        if os.path.exists(possible_dir):
            return os.path.relpath(possible_dir, root_dir).replace('\\', '/')

        # 2. Relative import from current file's directory
        curr_dir = os.path.dirname(os.path.abspath(current_file))
        possible_rel_path = os.path.join(curr_dir, *parts) + ".py"
        if os.path.exists(possible_rel_path):
            return os.path.relpath(possible_rel_path, root_dir).replace('\\', '/')
            
        possible_rel_dir = os.path.join(curr_dir, *parts, "__init__.py")
        if os.path.exists(possible_rel_dir):
            return os.path.relpath(possible_rel_dir, root_dir).replace('\\', '/')
            
        return None

    def _find_circular_dependencies(self, dep_graph: Dict[str, List[str]]) -> List[List[str]]:
        cycles = []
        visited = {} # node -> 0: unvisited, 1: visiting, 2: visited
        
        def dfs(node, path):
            visited[node] = 1
            path.append(node)
            for neighbor in dep_graph.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    cycle_start = path.index(neighbor)
                    cycle_chain = path[cycle_start:] + [neighbor]
                    is_dup = False
                    for existing in cycles:
                        if len(existing) == len(cycle_chain):
                            ext_str = "-".join(existing[:-1])
                            norm_str = "-".join(cycle_chain[:-1])
                            if any((ext_str in (norm_str + "-" + norm_str)) for _ in range(1)):
                                is_dup = True
                                break
                    if not is_dup:
                        cycles.append(cycle_chain)
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for node in dep_graph:
            if visited.get(node, 0) == 0:
                dfs(node, [])
        return cycles

    def _check_broken_local_imports(self, imports_list, root_dir: str, file_rel_path: str, all_rel_files: Set[str]) -> List[Issue]:
        issues = []
        for imp in imports_list:
            import_name = imp.name
            parts = import_name.split('.')
            first_part = parts[0]
            
            local_candidate_dir = os.path.join(root_dir, first_part)
            local_candidate_file = os.path.join(root_dir, first_part + ".py")
            
            if os.path.exists(local_candidate_dir) or os.path.exists(local_candidate_file):
                resolved_rel = self._resolve_import_to_local_file(import_name, root_dir, os.path.join(root_dir, file_rel_path))
                if resolved_rel is None:
                    issues.append(Issue(
                        title="Broken Local Import",
                        description=f"Local module '{import_name}' is imported in '{file_rel_path}' but could not be resolved to any file in the repository.",
                        severity="high",
                        category="bug",
                        line_number=imp.line_number,
                        code_snippet=f"import {import_name}",
                        suggestion=Suggestion(
                            original_code=f"import {import_name}",
                            proposed_code=f"# Fix import name or create the missing module '{import_name}'",
                            explanation="Importing modules that do not exist results in immediate runtime ImportError/ModuleNotFoundError."
                        )
                    ))
        return issues


