import ast
import os

def extract_functions_and_classes(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
            tree = ast.parse(content, filename=filepath)
        except Exception:
            return []

    items = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_info = {"name": node.name, "type": "Class", "docstring": ast.get_docstring(node), "methods": []}
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    class_info["methods"].append({
                        "name": n.name,
                        "docstring": ast.get_docstring(n)
                    })
            items.append(class_info)
        elif isinstance(node, ast.FunctionDef):
            items.append({
                "name": node.name,
                "type": "Function",
                "docstring": ast.get_docstring(node)
            })
    return items

def main():
    root_dir = r"c:\Users\karee\OneDrive\Desktop\random projects\graphics project\aetherbound"
    output_md = []
    output_md.append("\n## Data Flow")
    output_md.append("The core data flow in AetherBound follows a Data-Oriented Design. Data is loaded from `game_config.json` and `initial_state.json` via `data_manager.py`. It is stored in flat arrays within `PhysicsState` for vectorized processing by `gravity.py` and `collision.py`. In the main loop (`engine.py`), inputs are read via `input.py`, physics vectors are updated, and then the graphics components (`renderer.py` and `ui.py`) consume the state arrays to draw the frame.")
    
    output_md.append("\n## Detailed Function & Class Reference")
    
    for subdir, _, files in os.walk(root_dir):
        # Skip pycache and scratch
        if "__pycache__" in subdir or "scratch" in subdir:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                rel_path = os.path.relpath(filepath, root_dir)
                items = extract_functions_and_classes(filepath)
                if items:
                    output_md.append(f"\n### {rel_path.replace(os.sep, '/')}")
                    for item in items:
                        doc = item['docstring'] or "No docstring provided."
                        doc = doc.split('\n')[0] # just first line
                        if item['type'] == 'Class':
                            output_md.append(f"- **Class `{item['name']}`**: {doc}")
                            for m in item['methods']:
                                mdoc = m['docstring'] or "No docstring provided."
                                mdoc = mdoc.split('\n')[0]
                                output_md.append(f"  - **Method `{m['name']}`**: {mdoc}")
                        else:
                            output_md.append(f"- **Function `{item['name']}`**: {doc}")

    with open(os.path.join(root_dir, 'code_wiki.md'), 'a', encoding='utf-8') as f:
        f.write('\n'.join(output_md))
    print("Done")

if __name__ == '__main__':
    main()
