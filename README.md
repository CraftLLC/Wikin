# Wikin

A simple, beautiful documentation generator for Python. It extracts docstrings from functions and special comments from variables.

## Features

- **Function Docstrings**: Standard Python triple-quoted docstrings.
- **Variable Documentation**: 
  - `#: comment before variable`
  - `variable = value #: comment after variable`
- **Modern UI**: Clean, responsive HTML output with a premium look.
- **Markdown Support**: Use Markdown in your docstrings and comments.

## Installation

```bash
pip install .
```

## Usage

Run Wikin as a module:

```bash
python -m wikin <path_to_code> <project_name> <version>
```

Example:

```bash
python -m wikin ./ "My Project" 1.0.0
```

This will generate documentation in the `docs/index.html` file.

## Variable Documentation Example

```python
#: Number of requests per second
rpm = 10

timeout = 30 #: Connection timeout in seconds
```

Wikin will pick these up and include them in the generated documentation.
