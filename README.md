# Wikin

A simple, beautiful documentation generator for Python. It extracts docstrings from functions and special comments from variables.

## Features

- **Function Docstrings**: Standard Python triple-quoted docstrings.
- **Variable Documentation**: 
  - `#: comment before variable`
  - `variable = value #: comment after variable`
- **Global Search**: Instantly find functions, classes, and variables across all modules.
- **Multipage Mode**: Generate a clean landing page and separate files for each module.
- **Modern UI**: Clean, responsive HTML output with a premium glassmorphic look.
- **Markdown Support**: Use Markdown in your docstrings and comments.
- **Docstring Tables**: Automatically formats Google-style and NumPy-style parameters, attributes, and returns into elegant Markdown tables.
- **Addons (Themes & Plugins)**: Customize the look and feel with `.wikin` packaged CSS themes and JS plugins!
- **Custom Pages**: Easily inject `README` or dynamically parsed `LICENSE` files right into the sidebar.
- **Module Metadata**: Customize how modules appear in the documentation using a `Wikin:` block.

## Installation

```bash
pip install craftllc-wikin
```

## Usage

```bash
python -m wikin gen <path_to_code> <project_name> <version> [docs_folder]
```

Example:

```bash
python -m wikin gen ./ "My Project" 1.0.0
```

This will automatically parse the working directory and output standard HTML files to the customized `docs/` folder.

If you have `argcomplete` installed, Wikin offers full Tab autocomplete for CLI options! Need help? Just run:
```bash
python -m wikin help
```

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

## Configuration

You can fully orchestrate your generated suite by placing a `docs/.wikinconfig` (TOML format) directly inside your docs directory.

### Multipage & Custom Branding

For larger projects, switch into multipage mode to split generated pages. You can also hide the Wikin branded watermark!

```toml
[main]
multipage = true
show_generated_by = false
```

### Adding Project Links

To add helpful links (like GitHub, PyPI, or your website) to the sidebar, use the `[links]` section:

```toml
[links]
PyPI = "https://pypi.org/project/craftllc-wikin"
GitHub = "https://github.com/CraftLLC/Wikin"
```

### Custom Markdown Pages & Intelligent Licensing

Wikin allows you to seamlessly inject generic Markdown files right into your sidebar! 

```toml
[pages]
readme = "README.md"
license = "LICENSE"
license-parse = true
```

If `license-parse = true` is enabled, Wikin employs a versatile Regex parsing backend capable of correctly detecting **MIT, Apache 2.0, GNU GPL (v2/v3), BSD (2/3-Clause), MPL 2.0, WTFPL**, and more! It dynamically structures the Year, Type, and Author neatly above your license file.

### Themes & Plugins (Addons API)

Wikin supports community-provided ZIP addons formatted with `.wikin` extensions! Place these archives into `docs/addons/`. 

```toml
[addons]
themes = ["OLED"]
plugins = ["search_optimizer"]
```

These archives must contain a standard `manifest.json` mapped to their core `main_css` or `main_js` files. 

*Try our included `OLED.wikin` theme to transform the standard glassmorphic array into a completely flat, pure-black experience designed exclusively for organic LED developers.*

## Module Metadata Example

You can set a custom display name for your modules by adding a `Wikin:` block at the top of your module's docstring:

```python
"""
Wikin:
    name: Core Parser

This module handles all the parsing logic for Wikin.
"""
```

In the documentation, this module will be titled as **Core Parser (your_package.parser)**. The metadata block itself will be dynamically filtered from the description rendering.
