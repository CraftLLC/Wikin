"""
Wikin:
    name: Generator

Generates HTML documentation from parsed module data.
"""

import os
import markdown
import jinja2
try:
    import tomllib
except ImportError:
    # Fallback for Python < 3.11 if tomli is installed
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None
from typing import List
from .parser import ModuleDoc

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} v{{ version }}{% if current_module %} - {{ current_module.name }}{% endif %} - Documentation</title>
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
            z-index: 50;
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
        
        .brand a {
            text-decoration: none;
            color: inherit;
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

        h1, h2, h3, h4, h5, h6 {
            margin-bottom: 1.5rem;
            font-weight: 700;
            color: var(--text);
        }

        h1 { font-size: 2.5rem; margin-top: 0; }
        h2 { font-size: 1.8rem; margin-top: 3rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
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

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0 2rem 0;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            display: table;
        }

        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        th {
            background: rgba(255, 255, 255, 0.05);
            font-weight: 600;
            color: var(--accent);
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
        }

        td {
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        tr:last-child td {
            border-bottom: none;
        }

        td:first-child {
            font-family: 'Fira Code', monospace;
            font-weight: 500;
            color: var(--text);
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
            padding: 0.6rem 1rem 0.6rem 2.5rem;
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
            z-index: 10;
        }

        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--sidebar-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-top: 0.5rem;
            max-height: 400px;
            overflow-y: auto;
            display: none;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            z-index: 100;
        }

        .search-result-item {
            padding: 0.8rem 1rem;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
            text-decoration: none;
            display: block;
            color: inherit;
        }

        .search-result-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .search-result-item:last-child {
            border-bottom: none;
        }

        .search-result-name {
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
            color: var(--accent);
            display: block;
        }

        .search-result-type {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 0.2rem;
            display: block;
        }

        .search-result-module {
            font-size: 0.75rem;
            color: var(--primary);
            margin-bottom: 0.4rem;
            display: block;
        }

        /* Responsive */
        @media (max-width: 768px) {
            body { flex-direction: column; }
            aside { width: 100%; height: auto; position: static; }
            main { padding: 2rem; }
        }

        .project-links {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 2rem;
        }

        .project-link {
            flex: 1;
            min-width: fit-content;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            padding: 0.6rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            transition: all 0.2s;
            border: 1px solid var(--border);
            white-space: nowrap;
            line-height: normal;
        }

        .project-link:hover {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            transform: translateY(-1px);
        }
        {{ injected_css | safe }}
    </style>
    
    {% for t in themes_data %}
    <style class="wikin-theme-style" data-theme-id="{{ t.id }}" {% if theme_switcher %}disabled{% endif %}>
        {{ t.css | safe }}
    </style>
    {% endfor %}
    
    {% if theme_switcher %}
    <script>
        (function() {
            const savedTheme = localStorage.getItem('wikin-theme') || "{{ default_theme_id }}";
            document.querySelectorAll('.wikin-theme-style').forEach(s => {
                s.disabled = (s.getAttribute('data-theme-id') !== savedTheme);
            });
        })();
    </script>
    {% endif %}
</head>
<body>
    <aside>
        <div class="brand">
            <a href="{{ base_url }}index.html">{{ project_name }} <span class="version">v{{ version }}</span></a>
        </div>
        
        {% if links %}
        <div class="project-links">
            {% for name, url in links.items() %}
            <a href="{{ url }}" target="_blank" class="project-link">
                {{ name }}
            </a>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="search-container">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" id="wikin-search" class="search-input" placeholder="Search across all modules..." autocomplete="off">
            <div id="search-results" class="search-results"></div>
        </div>

        {% if theme_switcher %}
        <div class="theme-switcher-container" style="margin-bottom: 2rem;">
            <select id="theme-switcher" style="width: 100%; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border); color: var(--text); padding: 0.6rem; border-radius: 8px; font-family: inherit; font-size: 0.9rem; outline: none; cursor: pointer;">
                {% if not exclude_default_theme %}
                <option value="default">Standard Theme</option>
                {% endif %}
                {% for t in themes_data %}
                <option value="{{ t.id }}">{{ t.name }}</option>
                {% endfor %}
            </select>
        </div>
        {% endif %}

        <nav>
            {% if custom_pages %}
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); margin: 0 0 0.5rem 0.5rem; letter-spacing: 0.05em; font-weight: 600;">Pages</div>
            <ul id="sidebar-pages" style="margin-bottom: 2rem;">
                {% for page in custom_pages %}
                <li>
                    {% if multipage %}
                    <a href="{{ base_url }}{{ page.id }}.html"
                       class="{% if current_page and current_page.id == page.id %}active{% endif %}">
                        {{ page.title }}
                    </a>
                    {% else %}
                    <a href="#{{ page.id }}">{{ page.title }}</a>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); margin: 0 0 0.5rem 0.5rem; letter-spacing: 0.05em; font-weight: 600;">Modules</div>
            {% endif %}
            
            <ul id="sidebar-list">
                {% for mod in modules | sort(attribute='name') %}
                <li data-name="{{ mod.name }}">
                    <a href="{{ module_prefix }}{{ mod.original_name }}.html" 
                       class="{% if current_module and current_module.original_name == mod.original_name %}active{% endif %}">
                        {{ mod.name }}
                    </a>
                </li>
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
        {% if show_generated_by %}
        <p style="color: var(--text-muted); margin-bottom: 3rem;">Documentation generated by Wikin.</p>
        {% endif %}
        
        <div id="content-wrapper">
            {% if current_page %}
            <section class="doc-section searchable">
                {% if current_page.get('license_info') %}
                <div class="item" style="border-left: 4px solid var(--primary); margin-bottom: 2rem; background: rgba(99, 102, 241, 0.05);">
                    <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 1rem; font-weight: 600;">Detected License Properties</div>
                    <div style="display: flex; flex-direction: column; gap: 0.6rem;">
                        <div style="display: flex; align-items: center; gap: 0.8rem;"><strong style="color: var(--text); min-width: 80px;">Type:</strong> <span class="highlight" style="padding: 0.2rem 0.6rem; border-radius: 4px; font-weight: 600;">{{ current_page.license_info.type }}</span></div>
                        {% if current_page.license_info.year != 'Unknown' %}
                        <div style="display: flex; align-items: center; gap: 0.8rem;"><strong style="color: var(--text); min-width: 80px;">Year:</strong> <code>{{ current_page.license_info.year }}</code></div>
                        {% endif %}
                        {% if current_page.license_info.author != 'Unknown' %}
                        <div style="display: flex; align-items: center; gap: 0.8rem;"><strong style="color: var(--text); min-width: 80px;">Author / Owner:</strong> <span style="color: var(--accent); font-weight: 500;">{{ current_page.license_info.author }}</span></div>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
                {{ current_page.content | markdown | safe }}
            </section>
            {% elif not current_module and not multipage and custom_pages %}
                {% for page in custom_pages %}
                <section id="{{ page.id }}" class="doc-section searchable" data-name="{{ page.title }}">
                    {% if page.get('license_info') %}
                    <div class="item" style="border-left: 4px solid var(--primary); margin-bottom: 2rem; background: rgba(99, 102, 241, 0.05);">
                        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 1rem; font-weight: 600;">Detected License Properties</div>
                        <div style="display: flex; flex-direction: column; gap: 0.6rem;">
                            <div style="display: flex; align-items: center; gap: 0.8rem;"><strong style="color: var(--text); min-width: 80px;">Type:</strong> <span class="highlight" style="padding: 0.2rem 0.6rem; border-radius: 4px; font-weight: 600;">{{ page.license_info.type }}</span></div>
                            {% if page.license_info.year != 'Unknown' %}
                            <div style="display: flex; align-items: center; gap: 0.8rem;"><strong style="color: var(--text); min-width: 80px;">Year:</strong> <code>{{ page.license_info.year }}</code></div>
                            {% endif %}
                            {% if page.license_info.author != 'Unknown' %}
                            <div style="display: flex; align-items: center; gap: 0.8rem;"><strong style="color: var(--text); min-width: 80px;">Author / Owner:</strong> <span style="color: var(--accent); font-weight: 500;">{{ page.license_info.author }}</span></div>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                    {{ page.content | markdown | safe }}
                </section>
                {% endfor %}
            {% endif %}
            
            {% for mod in content_modules | sort(attribute='name') %}
            <section id="{{ mod.original_name | replace('.', '-') }}" class="doc-section" data-name="{{ mod.name }}">
                <h2>Module: {{ mod.name }}</h2>
                
                {% if mod.docstring %}
                <div class="module-doc searchable">{{ mod.docstring | markdown | safe }}</div>
                {% endif %}
                
                {% if mod.classes %}
                <div class="category-header"><h3>Classes</h3></div>
                {% for cls in mod.classes %}
                <div id="{{ mod.original_name | replace('.', '-') }}-{{ cls.name }}" class="item" data-name="{{ cls.name }}">
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
                    <div id="{{ mod.original_name | replace('.', '-') }}-{{ cls.name }}-{{ method.name }}" class="sub-item" data-name="{{ method.name }}" style="margin-left: 1.5rem; margin-top: 1rem; border-left: 2px solid var(--border); padding-left: 1rem;">
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
                <div id="{{ mod.original_name | replace('.', '-') }}-{{ func.name }}" class="item" data-name="{{ func.name }}">
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
                <div id="{{ mod.original_name | replace('.', '-') }}-{{ var.name }}" class="item" data-name="{{ var.name }}">
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
            
            {% if not current_module and not current_page and multipage %}
            <div class="welcome-section" style="text-align: center; padding: 4rem 0;">
                <h2 style="border: none;">Welcome to {{ project_name }} Documentation</h2>
                <p style="color: var(--text-muted); max-width: 600px; margin: 0 auto 2rem;">
                    Please select a module from the sidebar to view its detailed documentation.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; text-align: left;">
                    {% for mod in modules | sort(attribute='name') %}
                    <a href="modules/{{ mod.original_name }}.html" class="item" style="text-decoration: none; color: inherit; display: block;">
                        <span class="item-name">{{ mod.name }}</span>
                    </a>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </main>
    <script src="{{ base_url }}search_index.js"></script>
    <script>
        const searchInput = document.getElementById('wikin-search');
        const resultsDropdown = document.getElementById('search-results');
        const sections = document.querySelectorAll('.doc-section');
        const sidebarItems = document.querySelectorAll('#sidebar-list li');
        
        const base_url = "{{ base_url }}";
        const multipage = {{ 'true' if multipage else 'false' }};
        let modulesLoaded = false;
        let loadingPromise = null;

        function highlightMatch(text, query) {
            if (!query) return text;
            const regex = new RegExp(`(${query.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\\\\\\\$&")})`, 'gi');
            return text.replace(regex, '<span class="highlight">$1</span>');
        }

        async function loadAllModules() {
            if (modulesLoaded) return;
            if (loadingPromise) return loadingPromise;

            const manifest = window.WIKIN_MANIFEST;
            if (!manifest || !multipage) {
                modulesLoaded = true;
                return;
            }

            loadingPromise = Promise.all(manifest.modules.map(mod => {
                return new Promise((resolve) => {
                    const script = document.createElement('script');
                    script.src = `${base_url}modules/${mod.original_name}.data.js`;
                    script.onload = resolve;
                    script.onerror = resolve; // Continue even if one fails
                    document.head.appendChild(script);
                });
            })).then(() => {
                modulesLoaded = true;
            });

            return loadingPromise;
        }

        async function performGlobalSearch(query) {
            await loadAllModules();
            
            let searchIndex = window.WIKIN_SEARCH_INDEX;
            const manifest = window.WIKIN_MANIFEST;

            // If multipage, construct searchIndex from window.WIKIN_MODULE_... variables
            if (multipage && manifest) {
                searchIndex = {
                    modules: manifest.modules.map(m => {
                        const varName = `WIKIN_MODULE_${m.original_name.replace(/\./g, '_')}`;
                        return window[varName];
                    }).filter(m => !!m)
                };
            }

            if (!searchIndex || !query) {
                resultsDropdown.style.display = 'none';
                return;
            }

            const results = [];
            const q = query.toLowerCase();

            searchIndex.modules.forEach(mod => {
                const modId = mod.original_name.replace(/\./g, '-');
                const modUrl = multipage ? `${base_url}modules/${mod.original_name}.html` : `#${modId}`;
                
                // Check module
                if (mod.name.toLowerCase().includes(q) || (mod.docstring && mod.docstring.toLowerCase().includes(q))) {
                    results.push({
                        type: 'module',
                        name: mod.name,
                        module: mod.name,
                        url: modUrl,
                        score: mod.name.toLowerCase().includes(q) ? 10 : 1
                    });
                }

                // Check classes
                mod.classes.forEach(cls => {
                    const clsId = `${modId}-${cls.name}`;
                    const clsUrl = `${modUrl}#${clsId}`;
                    if (cls.name.toLowerCase().includes(q) || (cls.docstring && cls.docstring.toLowerCase().includes(q))) {
                        results.push({
                            type: 'class',
                            name: cls.name,
                            module: mod.name,
                            url: clsUrl,
                            score: cls.name.toLowerCase().includes(q) ? 8 : 1
                        });
                    }
                    if (cls.methods) {
                        cls.methods.forEach(method => {
                            const methodId = `${clsId}-${method.name}`;
                            if (method.name.toLowerCase().includes(q) || (method.docstring && method.docstring.toLowerCase().includes(q))) {
                                results.push({
                                    type: 'method',
                                    name: `${cls.name}.${method.name}`,
                                    module: mod.name,
                                    url: `${modUrl}#${methodId}`,
                                    score: method.name.toLowerCase().includes(q) ? 6 : 1
                                });
                            }
                        });
                    }
                });

                // Check functions
                mod.functions.forEach(func => {
                    const funcId = `${modId}-${func.name}`;
                    if (func.name.toLowerCase().includes(q) || (func.docstring && func.docstring.toLowerCase().includes(q))) {
                        results.push({
                            type: 'function',
                            name: func.name,
                            module: mod.name,
                            url: `${modUrl}#${funcId}`,
                            score: func.name.toLowerCase().includes(q) ? 7 : 1
                        });
                    }
                });

                // Check variables
                mod.variables.forEach(var_ => {
                    const varId = `${modId}-${var_.name}`;
                    if (var_.name.toLowerCase().includes(q) || (var_.docstring && var_.docstring.toLowerCase().includes(q))) {
                        results.push({
                            type: 'variable',
                            name: var_.name,
                            module: mod.name,
                            url: `${modUrl}#${varId}`,
                            score: var_.name.toLowerCase().includes(q) ? 5 : 1
                        });
                    }
                });
            });

            // Sort by score
            results.sort((a, b) => b.score - a.score);
            renderResults(results.slice(0, 15), query);
        }

        function renderResults(results, query) {
            if (results.length === 0) {
                resultsDropdown.innerHTML = '<div style="padding: 1rem; color: var(--text-muted); text-align: center;">No global matches found</div>';
                resultsDropdown.style.display = 'block';
                return;
            }

            resultsDropdown.innerHTML = '';
            results.forEach(res => {
                const div = document.createElement('a');
                div.className = 'search-result-item';
                div.href = res.url;
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span class="search-result-type">${res.type}</span>
                        <span class="search-result-module" style="margin-bottom: 0;">${res.module}</span>
                    </div>
                    <span class="search-result-name">${highlightMatch(res.name, query)}</span>
                `;
                div.onclick = () => {
                    resultsDropdown.style.display = 'none';
                    searchInput.value = '';
                };
                resultsDropdown.appendChild(div);
            });
            resultsDropdown.style.display = 'block';
        }

        searchInput.addEventListener('focus', () => {
            loadAllModules();
        });

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            if (query.length < 2) {
                resultsDropdown.style.display = 'none';
                return;
            }
            performGlobalSearch(query);
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !resultsDropdown.contains(e.target)) {
                resultsDropdown.style.display = 'none';
            }
        });
        {{ injected_js | safe }}
        
        {% if theme_switcher %}
        (function() {
            const select = document.getElementById('theme-switcher');
            if (!select) return;
            
            const styles = document.querySelectorAll('.wikin-theme-style');
            const savedTheme = localStorage.getItem('wikin-theme') || "{{ default_theme_id }}";
            select.value = savedTheme;
            
            select.addEventListener('change', (e) => {
                const themeId = e.target.value;
                styles.forEach(s => {
                    s.disabled = (s.getAttribute('data-theme-id') !== themeId);
                });
                localStorage.setItem('wikin-theme', themeId);
            });
        })();
        {% endif %}
    </script>
</body>
</html>
"""

class WikinGenerator:
    """
    Generates a premium-look HTML documentation from parsed module data.
    
    This class handles rendering the parsed Abstract Syntax Tree representation of Python 
    functions and configurations into a Jinja2 template with modern CSS formatting and Javascript 
    indexing for global search support.
    
    Attributes:
        project_name (str): The generic name of the documented project wrapper.
        version (str): The overarching software version of the package.
        config (dict): Cached configuration dictionary dynamically loaded via `.wikinconfig`.
        links (dict): Accessible project repository and interface navigational links wrapper.
        multipage (bool): Instructs if internal outputs should parse identically out independently generated sub-pages.
        env (jinja2.Environment): Central template-loading structure context.
        template (jinja2.Template): Resolved loaded Jinja2 primary processing file HTML wrapper.
    """
    def __init__(self, project_name: str, version: str, docs_dir: str = "docs"):
        """
        Initialize the generator with project metadata and configuration.
        
        This constructor initializes templating attributes, maps specific parsing mechanisms dynamically to Tomli structures, 
        and extracts custom routing commands externally parsed onto `.wikinconfig`. Contains logic to inject third-party '.wikin' plugin and theme ZIP archives.
        
        Args:
            project_name (str): Textual explicit descriptor specifying overarching package build scope title.
            version (str): The mapped tracking project versioning parameter sequence strings representation.
            docs_dir (str): Relative destination override target for generated documentation.
        """
        import zipfile
        import json
        self.project_name = project_name
        self.version = version
        self.docs_dir = docs_dir
        self.config = {}
        self.links = {}
        self.multipage = False
        self.custom_pages = []
        self.show_generated_by = True
        self.injected_css = ""
        self.injected_js = ""
        self.themes_data = []
        self.theme_switcher = False
        self.exclude_default_theme = False
        self.default_theme_id = "default"
        
        config_path = os.path.join(os.getcwd(), self.docs_dir, ".wikinconfig")
        if tomllib:
            if os.path.exists(config_path):
                try:
                    with open(config_path, "rb") as f:
                        self.config = tomllib.load(f)
                        self.links = self.config.get("links", {})
                        
                        main_cfg = self.config.get("main", {})
                        self.multipage = main_cfg.get("multipage", False)
                        self.show_generated_by = main_cfg.get("show_generated_by", True)
                        
                        addons_cfg = self.config.get("addons", {})
                        self.theme_switcher = addons_cfg.get("theme-switcher", False)
                        self.exclude_default_theme = addons_cfg.get("exclude-default-theme", False)
                        
                        pages_dict = self.config.get("pages", {})
                        license_parse = pages_dict.get("license-parse", False)
                        
                        for pid, path in pages_dict.items():
                            if pid == "license-parse":
                                continue
                            full_path = os.path.join(os.getcwd(), str(path))
                            if os.path.exists(full_path):
                                try:
                                    with open(full_path, "r", encoding="utf-8") as pf:
                                        content = pf.read()
                                        
                                        page_data = {
                                            "id": pid,
                                            "title": pid.replace('_', ' ').capitalize(),
                                            "content": content
                                        }
                                        
                                        if license_parse and pid.lower() == "license":
                                            import re
                                            info = {"type": "Unknown", "year": "Unknown", "author": "Unknown"}
                                            lower_content = content.lower()
                                            
                                            # Identify License Type
                                            if "mit license" in lower_content or "permission is hereby granted, free of charge" in lower_content:
                                                info["type"] = "MIT License"
                                            elif "apache license" in lower_content and "version 2.0" in lower_content:
                                                info["type"] = "Apache License 2.0"
                                            elif "gnu general public license" in lower_content and "version 3" in lower_content:
                                                info["type"] = "GNU GPL v3"
                                            elif "gnu general public license" in lower_content and "version 2" in lower_content:
                                                info["type"] = "GNU GPL v2"
                                            elif "gnu lesser general public license" in lower_content:
                                                info["type"] = "GNU LGPL"
                                            elif "gnu affero general public license" in lower_content:
                                                info["type"] = "GNU AGPL"
                                            elif "mozilla public license" in lower_content and "version 2.0" in lower_content:
                                                info["type"] = "MPL 2.0"
                                            elif "the unlicense" in lower_content or ("public domain" in lower_content and "unencumbered" in lower_content):
                                                info["type"] = "The Unlicense"
                                            elif "do what the fuck you want to public license" in lower_content or "wtfpl" in lower_content:
                                                info["type"] = "WTFPL"
                                            elif "creative commons zero" in lower_content or "cc0" in lower_content:
                                                info["type"] = "CC0 1.0 Universal"
                                            elif "eclipse public license" in lower_content:
                                                info["type"] = "Eclipse Public License"
                                            elif "redistribution and use in source and binary forms" in lower_content:
                                                info["type"] = "BSD 3-Clause License" if "neither the name" in lower_content else "BSD 2-Clause License"
                                            
                                            # Generically extract year and author across formats
                                            m = re.search(r'copyright\s*(?:\([cC]\))?\s*(\d{4}(?:-\d{4})?)\s+([^\n\r]+)', content, re.IGNORECASE)
                                            if m:
                                                info["year"] = m.group(1).strip()
                                                author_text = m.group(2).strip()
                                                # Strip common trailing lines
                                                author_text = re.sub(r'(\.|\,)?\s*(all rights reserved|licensed under|this program).*$', '', author_text, flags=re.IGNORECASE).strip()
                                                if len(author_text) > 40:
                                                    author_text = author_text[:40].strip() + "..."
                                                info["author"] = author_text
                                                
                                            page_data["license_info"] = info

                                        self.custom_pages.append(page_data)
                                except Exception as e:
                                    print(f"Warning: Could not read custom page {path}: {e}")
                                    
                        addons_cfg = self.config.get("addons", {})
                        themes = addons_cfg.get("themes", [])
                        plugins = addons_cfg.get("plugins", [])
                        
                        for addon_group, is_theme in [(themes, True), (plugins, False)]:
                            for addon_name in addon_group:
                                addon_path = os.path.join(os.getcwd(), self.docs_dir, "addons", f"{addon_name}.wikin")
                                if os.path.exists(addon_path):
                                    try:
                                        with zipfile.ZipFile(addon_path, 'r') as z:
                                            if "manifest.json" in z.namelist():
                                                manifest = json.loads(z.read("manifest.json").decode("utf-8"))
                                                css_file = manifest.get("main_css")
                                                js_file = manifest.get("main_js")
                                                
                                                if css_file and css_file in z.namelist():
                                                    content_css = z.read(css_file).decode("utf-8")
                                                    if is_theme:
                                                        self.themes_data.append({
                                                            "id": addon_name, 
                                                            "name": manifest.get("name", addon_name), 
                                                            "css": content_css
                                                        })
                                                    else:
                                                        self.injected_css += f"\n/* Addon [{addon_name}] */\n" + content_css
                                                        
                                                if js_file and js_file in z.namelist():
                                                    self.injected_js += f"\n/* Addon [{addon_name}] */\n" + z.read(js_file).decode("utf-8")
                                    except Exception as e:
                                        print(f"Warning: Failed to load addon {addon_name}: {e}")
                                else:
                                    print(f"Warning: Addon {addon_name} not found at {addon_path}")
                                    
                        if self.theme_switcher:
                            configured_default = addons_cfg.get("default-theme")
                            total_themes_count = len(self.themes_data) if self.exclude_default_theme else len(self.themes_data) + 1
                            
                            if total_themes_count > 2 and not configured_default:
                                print("Warning: 'default-theme' in [addons] is highly recommended (or mandatory) when providing multiple theme choices!")
                            
                            if configured_default:
                                self.default_theme_id = configured_default
                            elif self.exclude_default_theme and self.themes_data:
                                self.default_theme_id = self.themes_data[0]["id"]
                            else:
                                self.default_theme_id = "default"
                                    
                except Exception as e:
                    print(f"Warning: Failed to load .wikinconfig: {e}")
        else:
            if os.path.exists(config_path):
                print("Warning: .wikinconfig found, but 'tomli' is not installed. To parse config on Python < 3.11, run: pip install tomli")
        
        # Setup Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=True
        )
        self.env.filters['markdown'] = lambda x: markdown.markdown(x, extensions=['tables', 'fenced_code']) if x else ""
        self.template = self.env.from_string(HTML_TEMPLATE)

    def generate(self, modules: List[ModuleDoc], current_module: ModuleDoc = None, current_page: dict = None) -> str:
        """
        Transforms a list of ModuleDoc objects into an HTML string.
        
        Generates functional page-spanning document variables alongside specific individual target structures. 
        In dynamically triggered multipage operations, parses independently linked cross-path module references dynamically.
        
        Args:
            modules (List[ModuleDoc]): Parsed object structures retaining explicit hierarchical function-level context models.
            current_module (ModuleDoc, optional): If explicit single page operations are executing dynamically in multiprocessing tasks, denotes isolated file focus string wrappers. Defaults to None.
            current_page (dict, optional): Selected custom page output dynamically routing to template rendering engine.
            
        Returns:
            str: Substantially compiled raw output Jinja2 mapped HTML component configuration result sequence mapping wrapper.
        """
        content_modules = [current_module] if current_module else modules
        if current_module and self.multipage:
            # Individual module page
            base_url = "../"
            module_prefix = "./"
        elif current_page and self.multipage:
            # Custom page
            content_modules = []
            base_url = "./"
            module_prefix = "modules/"
        elif not current_module and not current_page and self.multipage:
            # Landing page (index.html)
            content_modules = []
            base_url = "./"
            module_prefix = "modules/"
        else:
            # Single page mode
            base_url = "./"
            module_prefix = "#"
            pass

        return self.template.render(
            project_name=self.project_name,
            version=self.version,
            modules=modules,
            content_modules=content_modules,
            links=self.links,
            custom_pages=self.custom_pages,
            multipage=self.multipage,
            current_module=current_module,
            current_page=current_page,
            base_url=base_url,
            module_prefix=module_prefix,
            injected_css=self.injected_css,
            injected_js=self.injected_js,
            show_generated_by=self.show_generated_by,
            themes_data=self.themes_data,
            theme_switcher=self.theme_switcher,
            exclude_default_theme=self.exclude_default_theme,
            default_theme_id=self.default_theme_id
        )

    def get_search_data(self, modules: List[ModuleDoc]) -> dict:
        """
        Serializes all module data into a dictionary for global search.
        
        Retained output is actively exposed within generated individual script templates supporting isolated index-focused contextual filtering logic mapping dependencies matching context instances.
        
        Args:
            modules (List[ModuleDoc]): Internal configuration structures generated across core abstract parsing elements sequentially parsing module context items linearly stringing parsed entities context paths values dict wrapper targets components structure representations mapping instances lists mappings target instance path elements.
            
        Returns:
            dict: Dataclass-converted multi-level structural format mapped indexing dict target search mappings matching variables dict outputs sequence configurations.
        """
        import dataclasses
        return {
            "project_name": self.project_name,
            "version": self.version,
            "modules": [dataclasses.asdict(m) for m in modules]
        }

    def save(self, html: str, output_path: str):
        """
        Saves the generated HTML to the specified file path.
        
        Instantiates any necessary sub-directories and commits rendered index outputs string elements files saving.
        
        Args:
            html (str): Complete multi-line template output sequence mapping structure.
            output_path (str): Relative destination targeting document sequence paths elements file references targets configurations formatting mapped instances target instance mapping path parameter configuration mapping structures mapping strings variables sequence variables string strings properties structure outputs mapped instances output mapped values lists formatting wrappers configuration values structural outputs maps structures templates formatting values strings strings paths configurations contexts contexts values contexts representations context implementations dict references implementations structures context environments objects files representations dependencies components instance mapping targets instances dependencies instance contexts formatting instance templates representations structures implementations values environments targets environments maps context properties paths parameters outputs configurations maps strings structural instances references settings references instance variables targets paths dependencies dependencies wrappers elements targets files elements mappings environments templates variables lists parameters mapping instance formats components strings values strings properties parameters paths paths mapped formats components configurations strings outputs configurations lists strings strings lists dependencies implementations formatting contexts targets environments instances representations formats parameters scripts configurations instances mapped configurations components mapped configurations dict references objects strings environments string variables formatting environments dependencies.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Documentation saved to {output_path}")
