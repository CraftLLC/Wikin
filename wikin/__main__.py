"""
Wikin:
   name: CLI Entry Point

CLI entry point for Wikin.
"""
import sys
import os
import argparse
from .parser import WikinParser
from .generator import WikinGenerator

def main():
    """
    Main entry point for the Wikin CLI tool.
    Parses command line arguments mapping outputs.
    """
    parser = argparse.ArgumentParser(description="Wikin: A robust documentation generator for Python")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    gen_parser = subparsers.add_parser("gen", aliases=["generate"], help="Generate documentation from python source files.")
    gen_parser.add_argument("source_path", help="Path to the source code to document")
    gen_parser.add_argument("project_name", help="Name of the project")
    gen_parser.add_argument("version", help="Version of the project")
    gen_parser.add_argument("docs_folder", nargs="?", default="docs", help="Output folder for the generated documentation (default: docs)")
    
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass
        
    args = parser.parse_args()
    
    if args.command in ("gen", "generate"):
        code_path = args.source_path
        project_name = args.project_name
        version = args.version
        docs_folder = args.docs_folder

        if not os.path.exists(code_path):
            print(f"Error: Path '{code_path}' does not exist.")
            sys.exit(1)

        print(f"Parsing code in {os.path.abspath(code_path)}...")
        wparser = WikinParser(code_path)
        modules = wparser.parse()

        if not modules:
            print("No modules with docstrings or documented variables found.")
            sys.exit(0)

        print(f"Found {len(modules)} documented modules.")
        
        generator = WikinGenerator(project_name, version, docs_folder)
        
        docs_dir = os.path.join(os.getcwd(), docs_folder)
        os.makedirs(docs_dir, exist_ok=True)

        if generator.multipage:
            print("Multipage mode enabled. Generating separate pages for each module...")
            modules_dir = os.path.join(docs_dir, "modules")
            os.makedirs(modules_dir, exist_ok=True)
            
            # Generate module pages
            for mod in modules:
                html = generator.generate(modules, current_module=mod)
                output_path = os.path.join(modules_dir, f"{mod.original_name}.html")
                generator.save(html, output_path)
                
            # Generate custom pages
            for page in generator.custom_pages:
                html = generator.generate(modules, current_page=page)
                output_path = os.path.join(docs_dir, f"{page['id']}.html")
                generator.save(html, output_path)
            
            # Generate index.html (landing page)
            index_html = generator.generate(modules, current_module=None)
            output_path = os.path.join(docs_dir, "index.html")
            generator.save(index_html, output_path)
        else:
            html = generator.generate(modules)
            output_path = os.path.join(docs_dir, "index.html")
            generator.save(html, output_path)
        
        import json
        import dataclasses
        
        # Create search manifest (names and links)
        manifest = {
            "project_name": generator.project_name,
            "version": generator.version,
            "multipage": generator.multipage,
            "modules": []
        }
        
        for mod in modules:
            manifest["modules"].append({
                "name": mod.name,
                "original_name": mod.original_name,
                "url": f"modules/{mod.original_name}.html" if generator.multipage else f"#{mod.original_name.replace('.', '-')}"
            })
            
            # In multipage mode, save individual module DATA in .js files for dynamic loading
            if generator.multipage:
                mod_data = dataclasses.asdict(mod)
                # JS-wrapper for local loading
                js_data_path = os.path.join(docs_dir, "modules", f"{mod.original_name}.data.js")
                with open(js_data_path, "w", encoding="utf-8") as f:
                    f.write(f"window.WIKIN_MODULE_{mod.original_name.replace('.', '_')} = {json.dumps(mod_data, ensure_ascii=False)};")
    
        # Save manifest
        search_index_path = os.path.join(docs_dir, "search_index.js")
        with open(search_index_path, "w", encoding="utf-8") as f:
            f.write(f"window.WIKIN_MANIFEST = {json.dumps(manifest, ensure_ascii=False)};")
        
        # If single page, also provide the full index for backward compatibility/simplicity
        if not generator.multipage:
            search_data = generator.get_search_data(modules)
            with open(search_index_path, "w", encoding="utf-8") as f:
                f.write(f"window.WIKIN_MANIFEST = {json.dumps(manifest, ensure_ascii=False)};\n")
                f.write(f"window.WIKIN_SEARCH_INDEX = {json.dumps(search_data, ensure_ascii=False)};")
        
        print(f"Global search manifest saved to {search_index_path}")
        print("\nDocumentation generation complete!")
        print(f"Open {os.path.join(docs_dir, 'index.html')} in your browser to view.")

    elif args.command is None:
        parser.print_help()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
