import re
import ast
import textwrap

def extract_boxed(response):
    match = re.search(r"\\boxed\{([^}]+)\}", response)
    if match:
        return match.group(1).strip()
    return ""

def split_into_entry_and_solution(code_str: str):
    tree = ast.parse(code_str)
    func_def = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)
    if not func_def:
        raise ValueError("No function definition found.")

    entry_point = func_def.name

    lines = code_str.splitlines()
    func_lineno = func_def.lineno - 1  # line number starts from 1
    body_lines = lines[func_lineno + 1:]
    body = "\n".join(body_lines)
    canonical_solution = textwrap.dedent(body).rstrip()

    return entry_point, canonical_solution

def format_check_function(assert_lines, entry_point, indent=4):
    indent_str = ' ' * indent
    check_lines = [f"def check({entry_point}):"]
    for line in assert_lines:
        check_lines.append(f"{indent_str}{line}")
    return "\n".join(check_lines)