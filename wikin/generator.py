import os
import markdown
import jinja2
from typing import List
from .parser import ModuleDoc

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} v{{ version }} - Documentation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg: #0f172a;
            --sidebar-bg: #1e293b;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(255, 255, 255, 0.1);
            --accent: #10b981;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        aside {
            width: 300px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border);
            padding: 2rem;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }

        .brand {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 2rem;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .version {
            font-size: 0.8rem;
            background: var(--primary);
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-weight: normal;
        }

        nav ul {
            list-style: none;
        }

        nav li {
            margin-bottom: 0.5rem;
        }

        nav a {
            color: var(--text-muted);
            text-decoration: none;
            transition: all 0.2s;
            font-size: 0.95rem;
            display: block;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
        }

        nav a:hover {
            color: var(--text);
            background: rgba(255, 255, 255, 0.05);
        }

        nav .active {
            color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
            font-weight: 500;
        }

        /* Main Content */
        main {
            flex: 1;
            padding: 3rem 5rem;
            max-width: 1000px;
            margin: 0 auto;
        }

        h1, h2, h3 {
            margin-bottom: 1.5rem;
            font-weight: 700;
        }

        h1 { font-size: 2.5rem; margin-top: 0; }
        h2 { font-size: 1.8rem; margin-top: 3rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; color: var(--primary); }
        h3 { font-size: 1.3rem; margin-top: 2rem; }

        .doc-section {
            margin-bottom: 4rem;
        }

        .item {
            background: var(--card-bg);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .item:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            border-color: rgba(99, 102, 241, 0.3);
        }

        .item-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }

        .item-name {
            font-family: 'Fira Code', monospace;
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--accent);
        }

        .item-type {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }

        .item-doc {
            font-size: 0.95rem;
            color: var(--text-muted);
        }

        code {
            font-family: 'Fira Code', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
        }

        pre {
            background: #000;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }

        pre code {
            background: transparent;
            padding: 0;
        }

        .signature {
            color: var(--primary);
            margin-bottom: 0.5rem;
            display: block;
            font-weight: 500;
        }

        .variable-value {
            font-family: 'Fira Code', monospace;
            color: #fb923c;
            margin-left: 0.5rem;
        }

        .category-header {
            margin-top: 3rem;
            margin-bottom: 1rem;
        }

        .highlight {
            background: rgba(99, 102, 241, 0.4);
            color: #fff;
            border-radius: 2px;
            padding: 0 1px;
        }

        .search-container {
            margin-bottom: 2rem;
            position: relative;
        }

        .search-input {
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.7rem 1rem 0.7rem 2.5rem;
            color: var(--text);
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-input:focus {
            border-color: var(--primary);
        }

        .search-icon {
            position: absolute;
            left: 0.8rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
        }

        /* Responsive */
        @media (max-width: 768px) {
            body { flex-direction: column; }
            aside { width: 100%; height: auto; position: static; }
            main { padding: 2rem; }
        }
    </style>
</head>
<body>
    <aside>
        <div class="brand">
            {{ project_name }} <span class="version">v{{ version }}</span>
        </div>
        
        <div class="search-container">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" id="wikin-search" class="search-input" placeholder="Search (names, docs, code)...">
        </div>

        <nav>
            <ul id="sidebar-list">
                {% for mod in modules | sort(attribute='name') %}
                <li data-name="{{ mod.name }}"><a href="#{{ mod.name | replace('.', '-') }}">{{ mod.name }}</a></li>
                {% endfor %}
            </ul>
        </nav>
    </aside>
    <main>
        <div id="no-results" style="display: none; text-align: center; margin-top: 5rem; color: var(--text-muted);">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="margin-bottom: 1rem; opacity: 0.5;">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <p>No results found for your search.</p>
        </div>

        <h1>{{ project_name }}</h1>
        <p style="color: var(--text-muted); margin-bottom: 3rem;">Documentation generated by Wikin.</p>
        
        <div id="content-wrapper">
            {% for mod in modules | sort(attribute='name') %}
            <section id="{{ mod.name | replace('.', '-') }}" class="doc-section" data-name="{{ mod.name }}">
                <h2>Module: {{ mod.name }}</h2>
                
                {% if mod.docstring %}
                <div class="module-doc searchable">{{ mod.docstring | markdown | safe }}</div>
                {% endif %}
                
                {% if mod.classes %}
                <div class="category-header"><h3>Classes</h3></div>
                {% for cls in mod.classes %}
                <div class="item" data-name="{{ cls.name }}">
                    <div class="item-header">
                        <div>
                            <span class="item-name searchable">{{ cls.name }}</span>
                            <span class="item-type">class</span>
                        </div>
                    </div>
                    {% if cls.docstring %}
                    <div class="item-doc searchable">{{ cls.docstring | markdown | safe }}</div>
                    {% endif %}
                    
                    {% for method in cls.methods %}
                    <div class="sub-item" data-name="{{ method.name }}" style="margin-left: 1.5rem; margin-top: 1rem; border-left: 2px solid var(--border); padding-left: 1rem;">
                        <div class="item-header">
                            <span class="item-name searchable" style="font-size: 0.9rem;">{{ method.name }}</span>
                            <span class="item-type" style="font-size: 0.6rem;">method</span>
                        </div>
                        <code class="signature searchable" style="font-size: 0.8rem;">{{ method.signature }}</code>
                        {% if method.docstring %}
                        <div class="item-doc searchable" style="font-size: 0.85rem;">{{ method.docstring | markdown | safe }}</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
                {% endif %}

                {% if mod.functions %}
                <div class="category-header"><h3>Functions</h3></div>
                {% for func in mod.functions %}
                <div class="item" data-name="{{ func.name }}">
                    <div class="item-header">
                        <div>
                            <span class="item-name searchable">{{ func.name }}</span>
                            <span class="item-type">function</span>
                        </div>
                    </div>
                    <code class="signature searchable">{{ func.signature }}</code>
                    {% if func.docstring %}
                    <div class="item-doc searchable">{{ func.docstring | markdown | safe }}</div>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}

                {% if mod.variables %}
                <div class="category-header"><h3>Variables</h3></div>
                {% for var in mod.variables %}
                <div class="item" data-name="{{ var.name }}">
                    <div class="item-header">
                        <div>
                            <span class="item-name searchable">{{ var.name }}</span>
                            <span class="item-type">variable</span>
                        </div>
                        <span class="variable-value">= {{ var.value }}</span>
                    </div>
                    {% if var.docstring %}
                    <div class="item-doc searchable">{{ var.docstring | markdown | safe }}</div>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}
                
            </section>
            {% endfor %}
        </div>
    </main>
    <script>
        const searchInput = document.getElementById('wikin-search');
        const sections = document.querySelectorAll('.doc-section');
        const sidebarItems = document.querySelectorAll('#sidebar-list li');
        const noResults = document.getElementById('no-results');
        
        // Cache original content for highlighting
        const searchables = document.querySelectorAll('.searchable');
        const originalContent = new Map();
        searchables.forEach((el, i) => {
            originalContent.set(el, el.innerHTML);
        });

        function highlight(el, query) {
            const original = originalContent.get(el);
            if (!query) {
                el.innerHTML = original;
                return false;
            }
            
            // Simple regex for highlighting while avoiding breaking HTML tags
            // This is a partial solution (doesn't handle nested tags well)
            // But good enough for docstrings and names
            const regex = new RegExp(`(${query})`, 'gi');
            let hasMatch = false;
            
            // To avoid matching inside HTML tags, we do a text nodes replacement
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = original;
            
            const walker = document.createTreeWalker(tempDiv, NodeFilter.SHOW_TEXT);
            const nodes = [];
            let node;
            while((node = walker.nextNode())) {
                nodes.push(node);
            }
            
            nodes.forEach(node => {
                const text = node.nodeValue;
                if (text && regex.test(text)) {
                    hasMatch = true;
                    const span = document.createElement('span');
                    span.innerHTML = text.replace(regex, '<span class="highlight">$1</span>');
                    node.parentNode.replaceChild(span, node);
                }
            });
            
            el.innerHTML = tempDiv.innerHTML;
            return hasMatch;
        }

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.toLowerCase().trim();
                let hasGlobalMatch = false;

                // Reset all highlighting first
                searchables.forEach(el => {
                    if (originalContent.has(el)) {
                        el.innerHTML = originalContent.get(el);
                    }
                });

                sections.forEach((section, idx) => {
                    const moduleName = section.getAttribute('data-name').toLowerCase();
                    const items = section.querySelectorAll('.item');
                    
                    let sectionMatch = moduleName.includes(query);
                    if (query) {
                        // Check module-level docstrings
                        section.querySelectorAll('.module-doc.searchable').forEach(el => {
                            if (highlight(el, query)) sectionMatch = true;
                        });
                    }

                    let anyItemMatch = false;

                    items.forEach(item => {
                        const itemName = item.getAttribute('data-name').toLowerCase();
                        let itemMatch = itemName.includes(query);
                        
                        // Highlight and check item-level names and docs
                        item.querySelectorAll(':scope > .item-header .searchable, :scope > .item-doc.searchable, :scope > .signature.searchable').forEach(el => {
                            if (highlight(el, query)) itemMatch = true;
                        });

                        const subItems = item.querySelectorAll('.sub-item');
                        let anySubMatch = false;

                        subItems.forEach(sub => {
                            let subMatch = sub.getAttribute('data-name').toLowerCase().includes(query);
                            sub.querySelectorAll('.searchable').forEach(el => {
                                if (highlight(el, query)) subMatch = true;
                            });

                            if (subMatch) {
                                sub.style.display = 'block';
                                anySubMatch = true;
                                itemMatch = true; // If a sub-item matches, its parent item should also be visible
                            } else {
                                // If query is active and no match in sub-item, hide it.
                                // Otherwise, show it (when query is empty or parent matches).
                                sub.style.display = (query && !itemMatch && !sectionMatch) ? 'none' : 'block';
                            }
                        });

                        if (itemMatch || anySubMatch || sectionMatch) { // Item is visible if it matches, or any of its sub-items match, or its parent section matches
                            item.style.display = 'block';
                            anyItemMatch = true;
                        } else {
                            item.style.display = 'none';
                        }
                    });

                    // Update category headers visibility
                    section.querySelectorAll('.category-header').forEach(h => {
                        let sibling = h.nextElementSibling;
                        let visible = false;
                        while (sibling && sibling.classList.contains('item')) {
                            if (sibling.style.display !== 'none') {
                                visible = true;
                                break;
                            }
                            sibling = sibling.nextElementSibling;
                        }
                        h.style.display = visible || sectionMatch ? 'block' : 'none';
                    });

                    if (sectionMatch || anyItemMatch) {
                        section.style.display = 'block';
                        sidebarItems[idx].style.display = 'block';
                        hasGlobalMatch = true;
                    } else {
                        section.style.display = 'none';
                        sidebarItems[idx].style.display = 'none';
                    }
                });

                noResults.style.display = hasGlobalMatch ? 'none' : 'block';
            }, 100);
        });
    </script>
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
        
        # Setup Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=True
        )
        self.env.filters['markdown'] = lambda x: markdown.markdown(x) if x else ""
        self.template = self.env.from_string(HTML_TEMPLATE)

    def generate(self, modules: List[ModuleDoc]) -> str:
        """
        Transforms a list of ModuleDoc objects into a single HTML string.
        """
        return self.template.render(
            project_name=self.project_name,
            version=self.version,
            modules=modules
        )

    def save(self, html: str, output_path: str):
        """
        Saves the generated HTML to the specified file path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Documentation saved to {output_path}")
