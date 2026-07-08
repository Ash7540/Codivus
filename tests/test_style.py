import pytest
import ast
from codereview.parsers.python import PythonParser
from codereview.style.pep8 import StyleAnalyzer

def test_naming_conventions():
    code = """
class bad_class_name:
    pass

class GoodClassName:
    pass

def BadFunctionName(camelCaseParam):
    badLocalVar = 1
    _fine_var = 2
    return badLocalVar

def good_function_name(snake_case_param):
    good_local_var = 1
    return good_local_var
"""
    parser = PythonParser()
    context = parser.parse_code(code, "naming_test.py")
    analyzer = StyleAnalyzer()
    issues = analyzer.analyze(context)
    
    class_issues = [i for i in issues if "Class Name" in i.title]
    func_issues = [i for i in issues if "Function Name" in i.title]
    param_issues = [i for i in issues if "Parameter Name" in i.title]
    var_issues = [i for i in issues if "Variable Name" in i.title]
    
    assert len(class_issues) == 1
    assert "bad_class_name" in class_issues[0].description
    
    assert len(func_issues) == 1
    assert "BadFunctionName" in func_issues[0].description
    
    assert len(param_issues) == 1
    assert "camelCaseParam" in param_issues[0].description
    
    assert len(var_issues) == 1
    assert "badLocalVar" in var_issues[0].description

def test_docstring_checks():
    # Module without docstring
    code = """
class GoodClass:
    # No docstring
    pass

class GoodClassWithDoc:
    \"\"\"This is a valid docstring.\"\"\"
    pass

def public_func():
    # No docstring
    pass

def public_func_with_doc():
    \"\"\"Valid docstring.\"\"\"
    pass

def _private_func():
    # No docstring, should not be flagged
    pass
"""
    parser = PythonParser()
    context = parser.parse_code(code, "doc_test.py")
    analyzer = StyleAnalyzer()
    issues = analyzer.analyze(context)
    
    mod_issues = [i for i in issues if "Module Docstring" in i.title]
    class_issues = [i for i in issues if "Class Docstring" in i.title]
    func_issues = [i for i in issues if "Function Docstring" in i.title]
    
    assert len(mod_issues) == 1
    assert len(class_issues) == 1
    assert len(func_issues) == 1

def test_formatting_and_length():
    # Overly long function: > 50 lines
    long_func_body = "\n".join([f"    x{i} = {i}" for i in range(60)])
    code = f"""
def overly_long_func():
{long_func_body}

class ComplexClass:
""" + "\n".join([f"    def method_{i}(self):\n        pass" for i in range(12)])

    
    parser = PythonParser()
    context = parser.parse_code(code, "format_test.py")
    analyzer = StyleAnalyzer()
    issues = analyzer.analyze(context)
    
    len_issues = [i for i in issues if i.title == "Overly Long Function"]
    class_issues = [i for i in issues if i.title == "Overly Complex Class Design"]
    
    assert len(len_issues) == 1
    assert "overly_long_func" in len_issues[0].description
    
    assert len(class_issues) == 1
    assert "ComplexClass" in class_issues[0].description

def test_python_best_practices():
    code = """
from os import *

def test_defaults(a, b=[], *, c={}):
    # Mutable defaults
    pass

def check_identity(x):
    # Unsafe literal identity comparisons
    if x is "abc":
        pass
    if x is not 123:
        pass
        
    # Safe comparisons
    if x is None:
        pass
    if x is True:
        pass
"""
    parser = PythonParser()
    context = parser.parse_code(code, "bp_test.py")
    analyzer = StyleAnalyzer()
    issues = analyzer.analyze(context)
    
    mutable_issues = [i for i in issues if i.title == "Mutable Default Argument"]
    wildcard_issues = [i for i in issues if i.title == "Wildcard Import Detected"]
    identity_issues = [i for i in issues if i.title == "Literal Identity Comparison"]
    
    # 2 parameters have mutable defaults (b and c)
    assert len(mutable_issues) == 2
    assert any("'b'" in i.description for i in mutable_issues)
    assert any("'c'" in i.description for i in mutable_issues)
    
    assert len(wildcard_issues) == 1
    assert "os" in wildcard_issues[0].description
    
    # 2 literal identity comparisons (is "abc" and is not 123)
    assert len(identity_issues) == 2
    assert any("is" in i.description for i in identity_issues)
    assert any("is not" in i.description for i in identity_issues)
