# Wikin

A simple, beautiful documentation generator for Python. It extracts docstrings from functions and special comments from variables.

## Features

- **Function Docstrings**: Standard Python triple-quoted docstrings.
- **Variable Documentation**: 
  - `#: comment before variable`
  - `variable = value #: comment after variable`
- **Modern UI**: Clean, responsive HTML output with a premium look.
- **Markdown Support**: Use Markdown in your docstrings and comments.
- **Module Metadata**: Customize how modules appear in the documentation using a `Wikin:` block.

## Installation

```bash
pip install craftllc-wikin
```

## Usage

```bash
wikin <path_to_code> <project_name> <version>
```

Example:

```bash
wikin ./ "My Project" 1.0.0
```

This will generate documentation in the `docs/index.html` file.

## Variable Documentation Example

```python
#: Number of requests per second
rpm = 10

timeout = 30 #: Connection timeout in seconds
```

Wikin will pick these up and include them in the generated documentation.

## Ignoring Files

To exclude specific files or directories from being processed, create a `.wikinignore` file in your `docs/` folder. It supports standard `.gitignore` (gitwildmatch) patterns.

**Example `docs/.wikinignore`:**

```text
# Ignore a specific file
secret_module.py

# Ignore an entire directory
internal_tools/

# Ignore all files with a certain extension
*.deprecated.py
```

## Module Metadata Example

You can set a custom display name for your modules by adding a `Wikin:` block at the top of your module's docstring:

```python
"""
Wikin:
    name: Core Parser

This module handles all the parsing logic for Wikin.
"""
```

In the documentation, this module will be titled as **Core Parser (your_package.parser)**. The metadata block itself will be hidden from the module's description.
