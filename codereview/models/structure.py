from typing import List, Optional
from pydantic import BaseModel

class ImportInfo(BaseModel):
    name: str
    alias: Optional[str] = None
    from_module: Optional[str] = None
    line_number: int

class FunctionInfo(BaseModel):
    name: str
    docstring: Optional[str] = None
    start_line: int
    end_line: int
    args: List[str]
    complexity: int = 1  # default to 1

class ClassInfo(BaseModel):
    name: str
    docstring: Optional[str] = None
    start_line: int
    end_line: int
    methods: List[FunctionInfo]
    bases: List[str]

class FileStats(BaseModel):
    loc: int
    comment_lines: int
    blank_lines: int
    num_functions: int
    num_classes: int

class CodeContext(BaseModel):
    file_path: str
    filename: str
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    docstring: Optional[str] = None  # module level docstring
    stats: FileStats
    source_code: str
