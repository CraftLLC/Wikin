"""
Wikin:
    name: Parser

Parser module for Wikin. Handles AST analysis of Python files.
"""
import ast
import os
import re
import tokenize
import io
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

        raw_docstring = ast.get_docstring(tree)
        display_name, cleaned_docstring = self._extract_metadata(raw_docstring, module_name)

        module_doc = ModuleDoc(
            name=display_name,
            path=file_path,
            docstring=cleaned_docstring
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

        # Extract variables with #: docstrings using tokenize
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
            
            # Type 2: Post-comment (e.g., var = val #: comment)
            # Find assignments followed by #: comment on the same line
            for i, tok in enumerate(tokens):
                if tok.type == tokenize.COMMENT and tok.string.startswith("#:"):
                    comment_text = tok.string[2:].strip()
                    row, col = tok.start
                    
                    # Search backwards on the same line for an assignment
                    # We expect: NAME = VALUE (maybe multiple tokens for value) #: COMMENT
                    j = i - 1
                    found_assignment = False
                    var_name = None
                    var_value_tokens = []
                    
                    while j >= 0 and tokens[j].start[0] == row:
                        if tokens[j].type == tokenize.OP and tokens[j].string == "=":
                            found_assignment = True
                            # The thing before '=' should be the name
                            if j > 0 and tokens[j-1].type == tokenize.NAME:
                                var_name = tokens[j-1].string
                            break
                        var_value_tokens.insert(0, tokens[j].string)
                        j -= 1
                    
                    if found_assignment and var_name:
                        # Extract the value string from tokens
                        val_str = "".join(var_value_tokens).strip()
                        module_doc.variables.append(VariableDoc(
                            name=var_name,
                            value=val_str,
                            docstring=comment_text
                        ))
                        continue

                # Type 1: Pre-comment (e.g., #: comment\nvar = val)
                if tok.type == tokenize.COMMENT and tok.string.startswith("#:"):
                    comment_text = tok.string[2:].strip()
                    row, col = tok.start
                    
                    # Search forward for the next NAME = ...
                    # Skip NEWLINE, NL, and other comments
                    j = i + 1
                    found_var = False
                    while j < len(tokens):
                        t = tokens[j]
                        if t.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT):
                            j += 1
                            continue
                        if t.type == tokenize.COMMENT:
                            # If we hit another comment, then this pre-comment applies to nothing or we chain?
                            # For now, let's say it stops.
                            break
                        
                        # Check for NAME =
                        if t.type == tokenize.NAME:
                            var_name = t.string
                            if j + 1 < len(tokens) and tokens[j+1].type == tokenize.OP and tokens[j+1].string == "=":
                                # Found it!
                                # Now get the value (until NEWLINE)
                                val_tokens = []
                                k = j + 2
                                while k < len(tokens) and tokens[k].type not in (tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT):
                                    val_tokens.append(tokens[k].string)
                                    k += 1
                                
                                module_doc.variables.append(VariableDoc(
                                    name=var_name,
                                    value="".join(val_tokens).strip(),
                                    docstring=comment_text
                                ))
                                found_var = True
                                break
                        break
                    if found_var:
                        continue
        except Exception as e:
            print(f"Warning: Tokenize failed for {file_path}: {e}")

        return module_doc

    def _extract_metadata(self, docstring: str, original_name: str) -> tuple[str, Optional[str]]:
        """
        Extracts Wikin-specific metadata from the module docstring.
        
        Args:
            docstring: The raw module docstring.
            original_name: The default dot-separated module name.
            
        Returns:
            tuple: (display_name, cleaned_docstring)
        """
        if not docstring:
            return original_name, docstring
        
        # Look for Wikin: block
        # Pattern matches "Wikin:" followed by indented lines
        pattern = r'(Wikin:\s*\n(?:\s+.*\n?)*)'
        match = re.search(pattern, docstring)
        
        display_name = original_name
        new_docstring = docstring
        
        if match:
            wikin_block = match.group(1)
            # Find 'name:' inside the block
            name_match = re.search(r'name:\s*(.*)', wikin_block)
            if name_match:
                custom_name = name_match.group(1).strip()
                display_name = f"{custom_name} ({original_name})"
            
            # Remove the metadata block from the docstring
            new_docstring = docstring.replace(wikin_block, "").strip()
            if not new_docstring:
                new_docstring = None
            
        return display_name, new_docstring

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
