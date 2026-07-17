import ast
from typing import List
from codereview.models import Issue, Suggestion


class CryptographyVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def visit_Call(self, node):
        # 1. Hashing checks: hashlib.md5(), hashlib.sha1(), md5(), sha1()
        is_weak_hash = False
        hash_func = ""

        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "hashlib"
            ):
                if node.func.attr in ("md5", "sha1"):
                    is_weak_hash = True
                    hash_func = f"hashlib.{node.func.attr}"
        elif isinstance(node.func, ast.Name):
            if node.func.id in ("md5", "sha1"):
                is_weak_hash = True
                hash_func = node.func.id

        if is_weak_hash:
            lineno = node.lineno
            snippet = (
                self.source_lines[lineno - 1]
                if 0 < lineno <= len(self.source_lines)
                else ""
            )
            self.issues.append(
                Issue(
                    title="Weak Cryptographic Hash Function",
                    description=(
                        f"Use of cryptographically weak hash function '{hash_func}' detected. "
                        "MD5 and SHA-1 are vulnerable to collision attacks and should not be used for security purposes."
                    ),
                    severity="medium",
                    category="security",
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code="import hashlib\n# Use SHA-256 or SHA-512 instead:\nhashlib.sha256(data)",
                        explanation="Using secure hashing functions like SHA-256 or SHA-512 makes it computationally infeasible to find collision matches.",
                    ),
                )
            )

        # 2. Cipher algorithm/mode checks: ECB mode, DES, ARC4, DES3, Blowfish
        is_weak_cipher = False
        cipher_detail = ""

        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == "modes" and node.func.attr == "ECB":
                    is_weak_cipher = True
                    cipher_detail = "AES ECB mode"
                elif node.func.value.id == "algorithms" and node.func.attr in (
                    "DES",
                    "DES3",
                    "ARC4",
                    "Blowfish",
                ):
                    is_weak_cipher = True
                    cipher_detail = f"algorithm {node.func.attr}"

            fullname = self._get_full_attribute_path(node.func)
            if fullname:
                if ".modes.ECB" in fullname:
                    is_weak_cipher = True
                    cipher_detail = "AES ECB mode"
                elif (
                    ".algorithms.DES" in fullname
                    or ".algorithms.DES3" in fullname
                    or ".algorithms.ARC4" in fullname
                    or ".algorithms.Blowfish" in fullname
                ):
                    is_weak_cipher = True
                    cipher_detail = "algorithm " + fullname.split(".")[-1]

        if is_weak_cipher:
            lineno = node.lineno
            snippet = (
                self.source_lines[lineno - 1]
                if 0 < lineno <= len(self.source_lines)
                else ""
            )
            self.issues.append(
                Issue(
                    title="Weak Cryptographic Cipher/Mode",
                    description=(
                        f"Use of insecure cryptographic {cipher_detail} detected. "
                        "DES, ARC4, and ECB mode are cryptographically weak and prone to decryption attacks."
                    ),
                    severity="high",
                    category="security",
                    line_number=lineno,
                    code_snippet=snippet.strip(),
                    suggestion=Suggestion(
                        original_code=snippet,
                        proposed_code="# Use AES with GCM or CBC mode, e.g.:\n# modes.GCM(nonce)",
                        explanation="Insecure cipher suites or block modes (like ECB, which doesn't hide patterns in plaintext) leak information. Use authenticated encryption modes like AES-GCM instead.",
                    ),
                )
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for name_node in node.names:
                if (
                    name_node.name in ("DES", "DES3", "ARC4", "Blowfish")
                    and "algorithms" in node.module
                ):
                    self._add_import_weak_issue(name_node.name, node.lineno)
                elif name_node.name == "ECB" and "modes" in node.module:
                    self._add_import_weak_issue("ECB mode", node.lineno)
        self.generic_visit(node)

    def _add_import_weak_issue(self, name: str, lineno: int):
        snippet = (
            self.source_lines[lineno - 1]
            if 0 < lineno <= len(self.source_lines)
            else ""
        )
        self.issues.append(
            Issue(
                title="Weak Cryptographic Cipher/Mode Imported",
                description=(
                    f"Import of insecure cryptographic component '{name}' detected. "
                    "Weak algorithms or modes should not be used in modern secure software."
                ),
                severity="high",
                category="security",
                line_number=lineno,
                code_snippet=snippet.strip(),
                suggestion=Suggestion(
                    original_code=snippet,
                    proposed_code="# Remove import and use secure cryptography primitives instead.",
                    explanation="Avoid importing weak cryptographic components to ensure compliance with modern security protocols.",
                ),
            )
        )

    def _get_full_attribute_path(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_full_attribute_path(node.value)
            if val:
                return f"{val}.{node.attr}"
        return ""


def detect_weak_cryptography(tree: ast.AST, source_lines: List[str]) -> List[Issue]:
    visitor = CryptographyVisitor(source_lines)
    visitor.visit(tree)
    return visitor.issues
