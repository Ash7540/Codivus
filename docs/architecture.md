# Architecture

This document describes the design principles and processing stages of the Codivus review engine.

## Flow Diagram

```mermaid
graph TD
    A[Start: review_file] --> B[AST Parser: get_parser_for_file]
    B --> C[Plugin Hook: on_review_start]
    C --> D[Cache Check: ReviewCache]
    D -- Hit --> E[Plugin Hook: on_review_end]
    E --> F[Return ReviewResult]
    D -- Miss --> G[Deterministic Static Analysis]
    G --> H[Run Custom Plugin Analysers]
    H --> I[Prompt Assembly: format_review_prompt]
    I --> J[Modify Prompt: modify_prompt plugins]
    J --> K[LLM Provider API execution]
    K --> L[Score & Deductions Recalculation]
    L --> M[Cache Set: Write JSON]
    M --> E
```

## Engine Components

1. **AST Parser Pipeline:** Translates standard code files into `CodeContext` structures capturing module functions, dependencies, classes, and statements.
2. **Deterministic Rules Engine:** Runs syntax complexity, PEP8 style violations, unused files, dead code, and security vulnerability patterns.
3. **Structured Provider Wrappers:** Interfaces formatting structured schemas (leveraging Pydantic parsing features where supported, or structured JSON schema instructions on fallbacks).
4. **Caching Layer:** Local hashing matching file contents, avoiding network calls for identical source files.
