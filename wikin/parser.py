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
import pathspec
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
    original_name: str
    path: str
    docstring: Optional[str] = None
    functions: List[FunctionDoc] = field(default_factory=list)
    variables: List[VariableDoc] = field(default_factory=list)
    classes: List[ClassDoc] = field(default_factory=list)

class WikinParser:
    """
    A parser that scans Python files for docstrings and specially formatted variable comments.
    
    This parser utilizes the built-in `ast` module to traverse Python files and extract classes,
    functions, methods, along with their docstrings and signatures.
    
    Attributes:
        root_dir (str): The root directory to scan for Python files.
        modules (list): A list of parsed module documentation objects.
        ignore_spec (PathSpec): A PathSpec object used to filter out ignored files based on `.wikinignore`.
    """
    def __init__(self, root_dir: str):
        """
        Initialize the parser with a root directory or a single file path.
        
        Args:
            root_dir (str): The target root directory path or file path from which to extract docs.
        """
        self.root_dir = os.path.abspath(root_dir)
        self.modules: List[ModuleDoc] = []
        self.ignore_spec = self._load_ignore_spec()

    def _load_ignore_spec(self) -> Optional[pathspec.PathSpec]:
        """
        Loads ignore patterns from docs/.wikinignore if it exists.
        
        Returns:
            Optional[pathspec.PathSpec]: A configured PathSpec if the ignore file is found, otherwise None.
        """
        ignore_file = Path(os.getcwd()) / "docs" / ".wikinignore"
        if ignore_file.exists():
            try:
                with open(ignore_file, "r", encoding="utf-8") as f:
                    return pathspec.PathSpec.from_lines('gitwildmatch', f)
            except Exception as e:
                print(f"Warning: Could not read {ignore_file}: {e}")
        return None

    def parse(self):
        """
        Perform a recursive search for Python files and extract documentation from them.
        
        This method walks through the root directory, identifies all valid Python files 
        (excluding those in junk directories or matched by the ignore spec), and parses 
        them to populate the internal modules list.
        
        Returns:
            List[ModuleDoc]: A list containing all uniquely documented modules found.
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
                   any(part in ('__pycache__', 'venv', 'env', 'dist', 'build', 'node_modules', 'site-packages', '.tox') for part in path.parts):
                    continue
                
                # Skip files matched by .wikinignore
                if self.ignore_spec:
                    # Match relative to the root_dir being scanned
                    rel_to_root = path.relative_to(root_path)
                    if self.ignore_spec.match_file(str(rel_to_root)):
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
        
        Extracts the module-level docstring, classes, functions, and specially annotated variables,
        formatting them with properties and typing information.
        
        Args:
            file_path (str): Path to the .py file.
            module_name (str): Dot-separated module name used for the documentation title.
            
        Returns:
            ModuleDoc: Module object containing extracted and grouped documentation structures.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ModuleDoc(name=module_name, original_name=module_name, path=file_path)

        raw_docstring = ast.get_docstring(tree)
        display_name, cleaned_docstring = self._extract_metadata(raw_docstring, module_name)

        module_doc = ModuleDoc(
            name=display_name,
            original_name=module_name,
            path=file_path,
            docstring=self._process_docstring(cleaned_docstring)
        )

        # Extract classes and functions
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    module_doc.functions.append(self._parse_function(node, source))
            
            elif isinstance(node, ast.ClassDef):
                class_docstring = ast.get_docstring(node)
                class_info = ClassDoc(name=node.name, docstring=self._process_docstring(class_docstring))
                
                # Extract methods from class
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_docstring = ast.get_docstring(subnode)
                        is_prop = False
                        for d in getattr(subnode, 'decorator_list', []):
                            if isinstance(d, ast.Name) and d.id == 'property':
                                is_prop = True
                            elif isinstance(d, ast.Attribute) and d.attr in ('setter', 'deleter'):
                                is_prop = True
                        
                        if method_docstring or is_prop:
                            class_info.methods.append(self._parse_function(subnode, source))
                
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
                            docstring=self._process_docstring(comment_text)
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
                                    docstring=self._process_docstring(comment_text)
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
        
        Allows modules to formally override their display name by including a special 
        YAML-like snippet in their root docstring block.
        
        Args:
            docstring (str): The raw module docstring block.
            original_name (str): The default dot-separated underlying module name.
            
        Returns:
            tuple: A tuple mapping `(display_name, cleaned_docstring)`.
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

    def _process_docstring(self, text: Optional[str]) -> str:
        """
        Parses Google and Numpy style docstrings and converts their sections into Markdown tables.
        
        This function sequentially detects specific section headers such as `Args:`, `Returns:`, and `Raises:` 
        to dynamically generate strict markdown tables inside the description string.
        
        Args:
            text (Optional[str]): The original unformatted docstring representation.
            
        Returns:
            str: Flow-processed docstring containing fully constructed Markdown table elements.
        """
        if not text:
            return ""
        
        lines = text.split('\n')
        out_lines = []
        state = "normal"
        table_lines = []
        headers = []
        
        def flush_table():
            if not table_lines: return []
            
            keep_cols = []
            for i, h in enumerate(headers[1:]):
                has_data = any(i < len(row) and str(row[i]).strip() for row in table_lines)
                if has_data or h != "Type":
                    keep_cols.append(i)
                    
            final_headers = [headers[i + 1] for i in keep_cols]
            
            res = [f"#### {headers[0]}", ""]
            res.append("| " + " | ".join(final_headers) + " |")
            res.append("|" + "|".join(["---"] * len(final_headers)) + "|")
            for row in table_lines:
                safe_row = [str(row[i]).replace('|', '\\|') if i < len(row) else "" for i in keep_cols]
                res.append("| " + " | ".join(safe_row) + " |")
            res.append("")
            table_lines.clear()
            headers.clear()
            return res

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            if state == "normal":
                if stripped in ('Args:', 'Arguments:', 'Parameters:', 'Keyword Args:', 'Keyword Arguments:', 'Attributes:', 'Properties:'):
                    out_lines.extend(flush_table())
                    headers = [stripped[:-1], "Name", "Type", "Description"]
                    state = "google_args"
                elif stripped in ('Returns:', 'Yields:', 'Raises:'):
                    out_lines.extend(flush_table())
                    headers = [stripped[:-1], "Type", "Description"]
                    state = "google_returns"
                elif i + 1 < len(lines) and stripped in ('Parameters', 'Returns', 'Yields', 'Raises', 'Attributes', 'Properties') and lines[i+1].strip() == '-' * len(stripped):
                    out_lines.extend(flush_table())
                    if stripped in ('Parameters', 'Attributes', 'Properties'):
                        headers = [stripped, "Name", "Type", "Description"]
                        state = "numpy_args"
                    else:
                        headers = [stripped, "Type", "Description"]
                        state = "numpy_returns"
                    i += 1
                else:
                    out_lines.append(line)
            
            elif state == "google_args":
                if not stripped:
                    out_lines.extend(flush_table()); state = "normal"
                elif line.startswith(' ') or line.startswith('\t'):
                    m = re.match(r'^\s+(\*\*?\w+)\s*\((.*?)\):\s*(.*)', line)
                    if not m: m = re.match(r'^\s+(\*\*?\w+):\s*(.*)', line)
                    if not m: m = re.match(r'^\s+([\w\.]+)\s*\((.*?)\):\s*(.*)', line)
                    if not m: m = re.match(r'^\s+([\w\.]+):\s*(.*)', line)
                    
                    if m:
                        if len(m.groups()) == 3: table_lines.append([m.group(1), m.group(2), m.group(3)])
                        else: table_lines.append([m.group(1), "", m.group(2)])
                    else:
                        if table_lines: table_lines[-1][-1] += " " + stripped
                        else: out_lines.extend(flush_table()); state = "normal"; out_lines.append(line)
                else:
                    out_lines.extend(flush_table()); state = "normal"; i -= 1
                    
            elif state == "google_returns":
                if not stripped:
                    out_lines.extend(flush_table()); state = "normal"
                elif line.startswith(' ') or line.startswith('\t'):
                    m = re.match(r'^\s+([^:]+):\s*(.*)', line)
                    if m: table_lines.append([m.group(1), m.group(2)])
                    else:
                        if table_lines: table_lines[-1][-1] += " " + stripped
                        else: table_lines.append(["", stripped])
                else:
                    out_lines.extend(flush_table()); state = "normal"; i -= 1
                    
            elif state == "numpy_args":
                if not stripped:
                    out_lines.extend(flush_table()); state = "normal"
                elif not (line.startswith(' ') or line.startswith('\t')):
                    m = re.match(r'^([^:]+)\s*:\s*(.*)', line)
                    if m: table_lines.append([m.group(1).strip(), m.group(2).strip(), ""])
                    else: table_lines.append([stripped, "", ""])
                else:
                    if table_lines:
                        if table_lines[-1][-1]: table_lines[-1][-1] += " " + stripped
                        else: table_lines[-1][-1] = stripped
                    else:
                        out_lines.extend(flush_table()); state = "normal"; out_lines.append(line)
                        
            elif state == "numpy_returns":
                if not stripped:
                    out_lines.extend(flush_table()); state = "normal"
                elif not (line.startswith(' ') or line.startswith('\t')):
                    table_lines.append([stripped, ""])
                else:
                    if table_lines:
                        if table_lines[-1][-1]: table_lines[-1][-1] += " " + stripped
                        else: table_lines[-1][-1] = stripped
                    else:
                        out_lines.extend(flush_table()); state = "normal"; out_lines.append(line)
            
            i += 1
            
        out_lines.extend(flush_table())
        return '\n'.join(out_lines).strip()

    def _parse_function(self, node: ast.AST, source: str) -> FunctionDoc:
        """
        Internal helper to create a FunctionDoc from an AST node.
        
        Constructs the full function formatting structure, building definitions containing type hints, 
        decorators (`@property`, `@classmethod`), async structures, and argument names.
        
        Args:
            node (ast.AST): The AST representation block dictating the function or method footprint.
            source (str): Processed full text representation of the file code, used specifically for matching exact inline python 3.8 constraints.
            
        Returns:
            FunctionDoc: Documented container including function's name wrapper, generated signature path, and attached processed docstring block.
        """
        signature_args = ""
        try:
            if hasattr(ast, 'unparse'):
                signature_args = ast.unparse(node.args)
            elif hasattr(ast, 'get_source_segment'):
                func_source = ast.get_source_segment(source, node)
                if func_source:
                    match = re.search(r'(?:async\s+)?def\s+[a-zA-Z0-9_]+\s*\((.*?)\)\s*(?:->.*?)?:', func_source, re.DOTALL)
                    if match:
                        signature_args = re.sub(r'\s+', ' ', match.group(1)).strip()
        except Exception:
            pass
            
        if not signature_args and hasattr(node, 'args') and hasattr(node.args, 'args'):
            args = [getattr(arg, 'arg', '') for arg in node.args.args]
            signature_args = ", ".join(args)

        prefix = ""
        is_prop = False
        is_setter = False
        is_deleter = False
        
        for d in getattr(node, 'decorator_list', []):
            if isinstance(d, ast.Name):
                if d.id == 'property':
                    is_prop = True
                elif d.id in ('classmethod', 'staticmethod'):
                    prefix += f"@{d.id} "
            elif isinstance(d, ast.Attribute):
                if d.attr == 'setter':
                    is_setter = True
                elif d.attr == 'deleter':
                    is_deleter = True

        if is_prop:
            prefix += "@property "
        elif is_setter:
            prefix += f"@{node.name}.setter "
        elif is_deleter:
            prefix += f"@{node.name}.deleter "

        if isinstance(node, ast.AsyncFunctionDef):
            prefix += "async "

        signature = f"{prefix}{node.name}({signature_args})"
        return FunctionDoc(
            name=node.name,
            signature=signature.strip(),
            docstring=self._process_docstring(ast.get_docstring(node))
        )
