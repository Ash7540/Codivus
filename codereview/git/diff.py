import re
from typing import Set


def parse_diff_added_lines(diff_text: str) -> Set[int]:
    """
    Parses a unified diff and returns a set of 1-indexed line numbers
    that were added or modified in the target file.
    """
    added_lines = set()
    current_line = 0

    # Matches hunk header: @@ -start,len +start,len @@
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for line in diff_text.splitlines():
        if line.startswith("@@"):
            match = hunk_re.match(line)
            if match:
                current_line = int(match.group(1))
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            added_lines.add(current_line)
            current_line += 1
        elif line.startswith("-"):
            # Deletion line, does not correspond to a line in the new version
            pass
        else:
            # Context line
            current_line += 1

    return added_lines
