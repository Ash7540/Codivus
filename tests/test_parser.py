import pytest
from codereview.parsers.python import PythonParser
from codereview.models.structure import CodeContext

def test_python_parser_success():
    sample_code = '''"""Module docstring example."""
import os
from typing import List, Optional as Opt

class ParentClass:
    pass

class MyClass(ParentClass, list):
    """Class docstring example."""
    def __init__(self, val: int, name: str = "test", *args, **kwargs) -> None:
        self.val = val

    async def run(self):
        # Nested comment line
        pass

def global_function(x, y):
    return x + y
'''

    parser = PythonParser()
    context = parser.parse_code(sample_code, "test_file.py")
    
    assert isinstance(context, CodeContext)
    assert context.filename == "test_file.py"
    assert context.docstring == "Module docstring example."

    # Verify imports
    assert len(context.imports) == 3
    
    imp_os = next(i for i in context.imports if i.name == "os")
    assert imp_os.from_module is None
    
    imp_list = next(i for i in context.imports if i.name == "List")
    assert imp_list.from_module == "typing"
    
    imp_opt = next(i for i in context.imports if i.name == "Optional")
    assert imp_opt.alias == "Opt"
    assert imp_opt.from_module == "typing"

    # Verify classes
    assert len(context.classes) == 2
    
    parent_cls = next(c for c in context.classes if c.name == "ParentClass")
    assert len(parent_cls.methods) == 0
    assert len(parent_cls.bases) == 0
    
    my_cls = next(c for c in context.classes if c.name == "MyClass")
    assert my_cls.docstring == "Class docstring example."
    assert my_cls.bases == ["ParentClass", "list"]
    assert len(my_cls.methods) == 2
    
    init_method = next(m for m in my_cls.methods if m.name == "__init__")
    assert init_method.args == ["self", "val", "name", "*args", "**kwargs"]
    assert init_method.docstring is None

    # Verify functions
    assert len(context.functions) == 1
    func = context.functions[0]
    assert func.name == "global_function"
    assert func.args == ["x", "y"]

    # Verify stats
    assert context.stats.num_classes == 2
    # 2 methods inside MyClass, 1 global function = 3 functions overall
    assert context.stats.num_functions == 3
    assert context.stats.comment_lines == 1
    assert context.stats.blank_lines == 4
    # Total lines: 18. 1 comment line, 4 blank lines => LOC = 13
    assert context.stats.loc == 13


def test_python_parser_syntax_error():
    sample_invalid_code = "def invalid_syntax(:"
    parser = PythonParser()
    context = parser.parse_code(sample_invalid_code, "invalid.py")
    
    assert isinstance(context, CodeContext)
    assert context.filename == "invalid.py"
    assert len(context.functions) == 0
    assert len(context.classes) == 0
    assert "Syntax Error" in context.docstring
    assert context.stats.loc == 1
