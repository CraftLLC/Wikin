"""
CLI entry point for Wikin.
"""
import sys
import os
from .parser import WikinParser
from .generator import WikinGenerator

def main():
    """
    Main entry point for the Wikin CLI tool.
    Parses command line arguments and initiates documentation generation.
    """
    if len(sys.argv) < 4:
        print("Usage: python -m wikin <path_to_code> <project_name> <version>")
        print("Example: python -m wikin ./ 'My Project' 1.0.0")
        sys.exit(1)

    code_path = sys.argv[1]
    project_name = sys.argv[2]
    version = sys.argv[3]

    if not os.path.exists(code_path):
        print(f"Error: Path '{code_path}' does not exist.")
        sys.exit(1)

    print(f"Parsing code in {os.path.abspath(code_path)}...")
    parser = WikinParser(code_path)
    modules = parser.parse()

    if not modules:
        print("No modules with docstrings or documented variables found.")
        sys.exit(0)

    print(f"Found {len(modules)} documented modules.")
    
    generator = WikinGenerator(project_name, version)
    html = generator.generate(modules)
    
    output_path = os.path.join(os.getcwd(), "docs", "index.html")
    generator.save(html, output_path)
    
    print("\nDocumentation generation complete!")
    print(f"Open {output_path} in your browser to view.")

if __name__ == "__main__":
    main()
