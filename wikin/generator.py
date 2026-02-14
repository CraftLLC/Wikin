"""
Generator module for Wikin. Handles HTML generation from documentation data.
"""
import os
import markdown
from typing import List
from .parser import ModuleDoc

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} v{version} - Documentation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg: #0f172a;
            --sidebar-bg: #1e293b;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(255, 255, 255, 0.1);
            --accent: #10b981;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            display: flex;
            min-height: 100vh;
        }}

        /* Sidebar */
        aside {{
            width: 300px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border);
            padding: 2rem;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }}

        .brand {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 2rem;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .version {{
            font-size: 0.8rem;
            background: var(--primary);
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-weight: normal;
        }}

        nav ul {{
            list-style: none;
        }}

        nav li {{
            margin-bottom: 0.5rem;
        }}

        nav a {{
            color: var(--text-muted);
            text-decoration: none;
            transition: all 0.2s;
            font-size: 0.95rem;
            display: block;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
        }}

        nav a:hover {{
            color: var(--text);
            background: rgba(255, 255, 255, 0.05);
        }}

        nav .active {{
            color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
            font-weight: 500;
        }}

        /* Main Content */
        main {{
            flex: 1;
            padding: 3rem 5rem;
            max-width: 1000px;
            margin: 0 auto;
        }}

        h1, h2, h3 {{
            margin-bottom: 1.5rem;
            font-weight: 700;
        }}

        h1 {{ font-size: 2.5rem; margin-top: 0; }}
        h2 {{ font-size: 1.8rem; margin-top: 3rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; color: var(--primary); }}
        h3 {{ font-size: 1.3rem; margin-top: 2rem; }}

        .doc-section {{
            margin-bottom: 4rem;
        }}

        .item {{
            background: var(--card-bg);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            border-color: rgba(99, 102, 241, 0.3);
        }}

        .item-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }}

        .item-name {{
            font-family: 'Fira Code', monospace;
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--accent);
        }}

        .item-type {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }}

        .item-doc {{
            font-size: 0.95rem;
            color: var(--text-muted);
        }}

        code {{
            font-family: 'Fira Code', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
        }}

        pre {{
            background: #000;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }}

        pre code {{
            background: transparent;
            padding: 0;
        }}

        .signature {{
            color: var(--primary);
            margin-bottom: 0.5rem;
            display: block;
            font-weight: 500;
        }}

        .variable-value {{
            font-family: 'Fira Code', monospace;
            color: #fb923c;
            margin-left: 0.5rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            body {{ flex-direction: column; }}
            aside {{ width: 100%; height: auto; position: static; }}
            main {{ padding: 2rem; }}
        }}
    </style>
</head>
<body>
    <aside>
        <div class="brand">
            {project_name} <span class="version">v{version}</span>
        </div>
        <nav>
            <ul>
                {sidebar_links}
            </ul>
        </nav>
    </aside>
    <main>
        <h1>{project_name}</h1>
        <p style="color: var(--text-muted); margin-bottom: 3rem;">Documentation generated by Wikin.</p>
        
        {content}
    </main>
</body>
</html>
"""

class WikinGenerator:
    """
    Generates a premium-look HTML documentation from parsed module data.
    """
    def __init__(self, project_name: str, version: str):
        """
        Initialize the generator with project metadata.
        """
        self.project_name = project_name
        self.version = version

    def generate(self, modules: List[ModuleDoc]) -> str:
        """
        Transforms a list of ModuleDoc objects into a single HTML string.
        """
        sidebar_links = ""
        content = ""

        for mod in sorted(modules, key=lambda x: x.name):
            anchor = mod.name.replace(".", "-")
            sidebar_links += f'<li><a href="#{anchor}">{mod.name}</a></li>'
            
            mod_section = f'<section id="{anchor}" class="doc-section">'
            mod_section += f'<h2>Module: {mod.name}</h2>'
            
            if mod.docstring:
                mod_section += f'<div class="module-doc">{markdown.markdown(mod.docstring)}</div>'
            
            if mod.classes:
                mod_section += '<h3>Classes</h3>'
                for cls in mod.classes:
                    methods_html = ""
                    for method in cls.methods:
                        methods_html += f"""
                        <div style="margin-left: 1.5rem; margin-top: 1rem; border-left: 2px solid var(--border); padding-left: 1rem;">
                            <div class="item-header">
                                <span class="item-name" style="font-size: 0.9rem;">{method.name}</span>
                                <span class="item-type" style="font-size: 0.6rem;">method</span>
                            </div>
                            <code class="signature" style="font-size: 0.8rem;">{method.signature}</code>
                            <div class="item-doc" style="font-size: 0.85rem;">{markdown.markdown(method.docstring)}</div>
                        </div>
                        """
                    
                    mod_section += f"""
                    <div class="item">
                        <div class="item-header">
                            <div>
                                <span class="item-name">{cls.name}</span>
                                <span class="item-type">class</span>
                            </div>
                        </div>
                        {f'<div class="item-doc">{markdown.markdown(cls.docstring)}</div>' if cls.docstring else ''}
                        {methods_html}
                    </div>
                    """

            if mod.functions:
                mod_section += '<h3>Functions</h3>'
                for func in mod.functions:
                    mod_section += f"""
                    <div class="item">
                        <div class="item-header">
                            <div>
                                <span class="item-name">{func.name}</span>
                                <span class="item-type">function</span>
                            </div>
                        </div>
                        <code class="signature">{func.signature}</code>
                        <div class="item-doc">{markdown.markdown(func.docstring)}</div>
                    </div>
                    """

            if mod.variables:
                mod_section += '<h3>Variables</h3>'
                for var in mod.variables:
                    mod_section += f"""
                    <div class="item">
                        <div class="item-header">
                            <div>
                                <span class="item-name">{var.name}</span>
                                <span class="item-type">variable</span>
                            </div>
                            <span class="variable-value">= {var.value}</span>
                        </div>
                        <div class="item-doc">{markdown.markdown(var.docstring)}</div>
                    </div>
                    """
            
            mod_section += "</section>"
            content += mod_section

        return HTML_TEMPLATE.format(
            project_name=self.project_name,
            version=self.version,
            sidebar_links=sidebar_links,
            content=content
        )

    def save(self, html: str, output_path: str):
        """
        Saves the generated HTML to the specified file path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Documentation saved to {output_path}")
