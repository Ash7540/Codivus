from typing import List
from codereview.analyzers.base import BaseAnalyzer
from codereview.models import Issue, Suggestion, CodeContext


class DuplicationAnalyzer(BaseAnalyzer):
    def __init__(self, min_lines: int = 5):
        self.min_lines = min_lines

    def analyze(self, context: CodeContext) -> List[Issue]:
        issues = []
        lines = context.source_code.splitlines()

        # Clean lines, keeping map to original line number
        cleaned = []
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Ignore empty lines and comment lines
            if stripped and not stripped.startswith("#"):
                # Strip all inner whitespaces to match lines regardless of formatting differences
                normalized = "".join(stripped.split())
                cleaned.append((idx, normalized, line))

        n = len(cleaned)
        matched_indices = set()  # Track indices in 'cleaned' that are already flagged

        for i in range(n):
            if i in matched_indices:
                continue
            for j in range(i + self.min_lines, n):
                if j in matched_indices:
                    continue

                # Calculate match length
                match_len = 0
                while (
                    i + match_len < j
                    and j + match_len < n
                    and cleaned[i + match_len][1] == cleaned[j + match_len][1]
                ):
                    match_len += 1

                if match_len >= self.min_lines:
                    # Retrieve original lines for the snippet
                    start_line_i = cleaned[i][0]
                    start_line_j = cleaned[j][0]
                    end_line_i = cleaned[i + match_len - 1][0]

                    dup_snippet = "\n".join(lines[start_line_i - 1 : end_line_i])

                    # Mark all matched indices to avoid subsets / overlapping reports
                    for k in range(match_len):
                        matched_indices.add(i + k)
                        matched_indices.add(j + k)

                    issues.append(
                        Issue(
                            title="Duplicate Code Block",
                            description=(
                                f"Identical code sequence of {match_len} lines detected. "
                                f"Matches the code block starting at line {start_line_i}."
                            ),
                            severity="medium",
                            category="style",
                            line_number=start_line_j,
                            code_snippet=dup_snippet,
                            suggestion=Suggestion(
                                original_code=dup_snippet,
                                proposed_code="# Consider extracting this duplicate logic into a shared helper function.",
                                explanation="Duplicated code increases codebase size and complicates bug fixes. Consolidating into helper functions is recommended.",
                            ),
                        )
                    )
                    # Move to next outer loop iteration
                    break

        return issues
