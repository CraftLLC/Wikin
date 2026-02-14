"""
Parser module for Wikin. Handles AST analysis of Python files.
"""
import ast
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class VariableDoc:
    name: str
    value: str
    docstring: str

@dataclass
class FunctionDoc:
    name: str
    signature: str
    docstring: str

@dataclass
class ClassDoc:
    name: str
    docstring: str
    methods: List[FunctionDoc] = field(default_factory=list)

@dataclass
class ModuleDoc:
    """
    Holds documentation data for a single Python module.
    """
    name: str
    path: str
    docstring: Optional[str] = None
    functions: List[FunctionDoc] = field(default_factory=list)
    variables: List[VariableDoc] = field(default_factory=list)
    classes: List[ClassDoc] = field(default_factory=list)

class WikinParser:
    """
    A parser that scans Python files for docstrings and specially formatted variable comments.
    """
    def __init__(self, root_dir: str):
        """
        Initialize the parser with a root directory or a single file path.
        """
        self.root_dir = os.path.abspath(root_dir)
        self.modules: List[ModuleDoc] = []

    def parse(self):
        """
        Perform a recursive search for Python files and extract documentation from them.
        
        Returns:
            List[ModuleDoc]: A list of documented modules found.
        """
        root_path = Path(self.root_dir)
        py_files = []
        
        if root_path.is_file():
            if root_path.suffix == ".py":
                py_files.append(root_path)
            else:
                print(f"Error: {root_path} is not a Python file.")
                return []
        else:
            # Recursive search for all .py files
            for path in root_path.rglob("*.py"):
                # Skip junk directories
                if any(part.startswith('.') for part in path.parts) or \
                   any(part in ('__pycache__', 'venv', 'env', 'dist', 'build') for part in path.parts):
                    continue
                py_files.append(path)

        if not py_files:
            print(f"No .py files found in {self.root_dir}")
            return []

        print(f"Found {len(py_files)} Python files. Scanning for docstrings...")
        
        for full_path in py_files:
            rel_path = full_path.relative_to(root_path) if root_path.is_dir() else full_path.name
            
            # Normalize module name
            module_name = str(rel_path).replace("\\", ".").replace("/", ".").replace(".py", "")
            
            if module_name == "__init__" or module_name == "":
                module_name = root_path.resolve().name
            elif module_name.endswith(".__init__"):
                module_name = module_name[:-9]
            
            print(f"Parsing module: {module_name} ({rel_path})")
            
            try:
                module_doc = self._parse_file(str(full_path), module_name)
                if module_doc.functions or module_doc.variables or module_doc.docstring or module_doc.classes:
                    self.modules.append(module_doc)
            except Exception as e:
                print(f"Warning: Could not parse {full_path}: {e}")
        
        return self.modules

    def _parse_file(self, file_path: str, module_name: str) -> ModuleDoc:
        """
        Parses a single Python file using the ast module.
        
        Args:
            file_path: Path to the .py file.
            module_name: Dot-separated module name.
            
        Returns:
            ModuleDoc containing extracted documentation.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ModuleDoc(name=module_name, path=file_path)

        module_doc = ModuleDoc(
            name=module_name,
            path=file_path,
            docstring=ast.get_docstring(tree)
        )

        # Extract classes and functions
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    module_doc.functions.append(self._parse_function(node))
            
            elif isinstance(node, ast.ClassDef):
                class_docstring = ast.get_docstring(node)
                class_info = ClassDoc(name=node.name, docstring=class_docstring or "")
                
                # Extract methods from class
                for subnode in node.body:
                    if isinstance(subnode, ast.FunctionDef):
                        method_docstring = ast.get_docstring(subnode)
                        if method_docstring:
                            class_info.methods.append(self._parse_function(subnode))
                
                if class_info.docstring or class_info.methods:
                    module_doc.classes.append(class_info)

        # Extract variables with #: docstrings
        # We need to scan the lines for #: comments
        lines = source.splitlines()
        
        # Two types of variable docs:
        # Type 1: #: Doc before\nvar = val
        # Type 2: var = val #: Doc after
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip lines that are just string literals containing #: (like in our own code)
            if 'if "#:" in line' in line or 'line.split("#:", 1)' in line:
                continue

            # Type 2: Post-comment (e.g., var = val #: comment)
            if "#:" in line and "=" in line:
                # Basic check to avoid matching #: inside strings
                # This is a bit naive but covers many cases
                parts = line.split("#:", 1)
                code_part = parts[0].strip()
                comment_part = parts[1].strip()
                
                if "=" in code_part and not code_part.startswith("#"):
                    var_name_part = code_part.split("=", 1)[0].strip()
                    # Check if it's a simple name
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name_part):
                        module_doc.variables.append(VariableDoc(
                            name=var_name_part,
                            value=code_part.split("=", 1)[1].strip(),
                            docstring=comment_part
                        ))
                        continue

            # Type 1: Pre-comment (e.g., #: comment\nvar = val)
            if stripped.startswith("#:"):
                comment = stripped[2:].strip()
                # Look at next line(s) for assignment
                next_idx = i + 1
                while next_idx < len(lines):
                    next_line = lines[next_idx].strip()
                    if not next_line or next_line.startswith("#"):
                        next_idx += 1
                        continue
                    if "=" in next_line:
                        var_name_part = next_line.split("=", 1)[0].strip()
                        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name_part):
                            module_doc.variables.append(VariableDoc(
                                name=var_name_part,
                                value=next_line.split("=", 1)[1].strip(),
                                docstring=comment
                            ))
                        break
                    else:
                        break

        return module_doc

    def _parse_function(self, node: ast.FunctionDef) -> FunctionDoc:
        """
        Internal helper to create a FunctionDoc from an AST node.
        """
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        signature = f"{node.name}({', '.join(args)})"
        return FunctionDoc(
            name=node.name,
            signature=signature,
            docstring=ast.get_docstring(node) or ""
        )
