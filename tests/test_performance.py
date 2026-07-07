import pytest
import ast
from codereview.parsers.python import PythonParser
from codereview.performance.profiler import PerformanceAnalyzer

def test_loop_performance():
    code = """
def process_data(items):
    # 1. String concat in loop
    res = ""
    for item in items:
        res += str(item)
        
    # 2. Database execute in loop
    for item in items:
        cursor.execute("INSERT INTO log VALUES (?)", (item,))
        
    # 3. HTTP request in loop
    for item in items:
        requests.get(f"https://api.example.com/items/{item}")
        
    # Safe loop
    parts = []
    for item in items:
        parts.append(str(item))
    res = "".join(parts)
"""
    parser = PythonParser()
    context = parser.parse_code(code, "loop_test.py")
    analyzer = PerformanceAnalyzer()
    issues = analyzer.analyze(context)
    
    concat_issues = [i for i in issues if i.title == "String Concatenation in Loop"]
    expensive_issues = [i for i in issues if i.title == "Expensive Operation in Loop"]
    
    assert len(concat_issues) == 1
    assert concat_issues[0].severity == "medium"
    assert "res" in concat_issues[0].description
    
    assert len(expensive_issues) == 2
    assert any("Database" in i.description for i in expensive_issues)
    assert any("HTTP" in i.description for i in expensive_issues)

def test_memory_performance():
    code = """
def file_and_agg():
    # 1. Memory-inefficient file read
    with open("data.txt", "r") as f:
        content = f.read()
        
    # 2. Unnecessary list comprehension in aggregation
    total = sum([x * 2 for x in range(100)])
    
    # Safe chunk read
    with open("data.txt", "r") as f:
        chunk = f.read(1024)
        
    # Safe generator expression
    total_safe = sum(x * 2 for x in range(100))
"""
    parser = PythonParser()
    context = parser.parse_code(code, "mem_test.py")
    analyzer = PerformanceAnalyzer()
    issues = analyzer.analyze(context)
    
    read_issues = [i for i in issues if i.title == "Memory-Inefficient File Read"]
    agg_issues = [i for i in issues if i.title == "Unnecessary List Comprehension in Aggregation"]
    
    assert len(read_issues) == 1
    assert read_issues[0].severity == "medium"
    
    assert len(agg_issues) == 1
    assert agg_issues[0].severity == "medium"
    assert "sum" in agg_issues[0].description

def test_async_performance():
    code = """
import asyncio
import time
import requests

async def main_async(tasks):
    # 1. Blocking sleep in async
    time.sleep(1)
    
    # 2. Blocking requests call in async
    requests.get("https://google.com")
    
    # 3. Sequential await in loop
    for t in tasks:
        await t
        
    # Safe async sleep
    await asyncio.sleep(1)
"""
    parser = PythonParser()
    context = parser.parse_code(code, "async_test.py")
    analyzer = PerformanceAnalyzer()
    issues = analyzer.analyze(context)
    
    blocking_issues = [i for i in issues if i.title == "Blocking Call in Async Function"]
    seq_issues = [i for i in issues if i.title == "Sequential Await in Loop"]
    
    assert len(blocking_issues) == 2
    assert any("time.sleep" in i.description for i in blocking_issues)
    assert any("blocking sync call" in i.description for i in blocking_issues)
    
    assert len(seq_issues) == 1
    assert seq_issues[0].severity == "medium"

def test_membership_performance():
    code = """
def test_search():
    my_list = [1, 2, 3, 4, 5]
    
    # 1. Membership check on list
    if 3 in my_list:
        print("found")
        
    # Safe set conversion
    my_set = set(my_list)
    if 3 in my_set:
        print("found")
"""
    parser = PythonParser()
    context = parser.parse_code(code, "search_test.py")
    analyzer = PerformanceAnalyzer()
    issues = analyzer.analyze(context)
    
    member_issues = [i for i in issues if i.title == "Membership Check on List"]
    
    assert len(member_issues) == 1
    assert member_issues[0].severity == "low"
    assert "my_list" in member_issues[0].description
