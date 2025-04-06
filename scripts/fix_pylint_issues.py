#!/usr/bin/env python3
"""
Automatic pylint issue fixer for har-oa3-converter.

This script fixes common pylint issues:
1. Remove unused imports
2. Fix unnecessary pass statements in abstract methods
3. Replace unnecessary elif after return statements
4. Fix bare except blocks
"""

import os
import re
import sys
from pathlib import Path


DIRECTORIES_TO_FIX = [
    "har_oa3_converter",
    "tests",
]


def fix_unused_imports(file_path, content):
    """Remove unused imports identified by pylint."""
    # Pattern for imports
    import_pattern = re.compile(r"^import ([\w, ]+)|^from ([\w.]+) import ([\w, \(\)\n]+)", re.MULTILINE)
    
    # Pylint unused import message format
    unused_pattern = re.compile(r"W0611: Unused ([\w]+) imported from ([\w.]+)|W0611: Unused import ([\w]+)")
    
    # Run pylint to get unused imports
    import subprocess
    result = subprocess.run(
        ["pylint", "--disable=all", "--enable=unused-import", file_path],
        capture_output=True,
        text=True
    )
    
    unused_imports = set()
    
    # Extract unused imports from pylint output
    for line in result.stdout.split("\n"):
        match = unused_pattern.search(line)
        if match:
            if match.group(1) and match.group(2):  # from X import Y form
                unused_imports.add((match.group(2), match.group(1)))
            elif match.group(3):  # import X form
                unused_imports.add((None, match.group(3)))
    
    if not unused_imports:
        return content
    
    # Process each import statement
    for match in import_pattern.finditer(content):
        if match.group(1):  # import X form
            imports = [imp.strip() for imp in match.group(1).split(",")]
            updated_imports = [imp for imp in imports if (None, imp) not in unused_imports]
            if not updated_imports:
                # Remove entire line
                content = content.replace(match.group(0), "")
            elif len(updated_imports) < len(imports):
                # Remove specific imports
                content = content.replace(
                    match.group(0),
                    f"import {', '.join(updated_imports)}"
                )
        elif match.group(2) and match.group(3):  # from X import Y form
            module = match.group(2)
            if "(" in match.group(3):
                # Multi-line imports
                imports_text = match.group(3).strip()
                # Extract individual imports
                imports = re.findall(r"\b([\w]+)\b", imports_text)
                updated_imports = [imp for imp in imports if (module, imp) not in unused_imports]
                if not updated_imports:
                    # Remove entire import statement
                    content = content.replace(match.group(0), "")
                elif len(updated_imports) < len(imports):
                    # Rebuild the import statement
                    if len(updated_imports) > 1:
                        new_import = f"from {module} import (\n    {',\n    '.join(updated_imports)}\n)"
                    else:
                        new_import = f"from {module} import {updated_imports[0]}"
                    content = content.replace(match.group(0), new_import)
            else:
                # Single line imports
                imports = [imp.strip() for imp in match.group(3).split(",")]
                updated_imports = [imp for imp in imports if (module, imp) not in unused_imports]
                if not updated_imports:
                    # Remove entire line
                    content = content.replace(match.group(0), "")
                elif len(updated_imports) < len(imports):
                    # Remove specific imports
                    content = content.replace(
                        match.group(0),
                        f"from {module} import {', '.join(updated_imports)}"
                    )
    
    return content


def fix_unnecessary_pass(content):
    """Remove unnecessary pass statements in abstract methods."""
    # Find abstract methods with unnecessary pass
    abstract_pattern = re.compile(
        r"@abstractmethod[^\n]*\n\s+def [^\n]+:\n[^\n]*\"\"\".+?\"\"\".+?\n\s+pass", 
        re.DOTALL
    )
    
    # Remove the 'pass' statement
    for match in abstract_pattern.finditer(content):
        method_code = match.group(0)
        fixed_code = re.sub(r"\n\s+pass$", "", method_code)
        content = content.replace(method_code, fixed_code)
    
    return content


def fix_unnecessary_elif_after_return(content):
    """Replace unnecessary elif after return statements."""
    # Pattern to match 'return X\n    elif' pattern
    pattern = re.compile(r"(\s+)return [^\n]+\n\1elif")
    
    # Replace 'elif' with 'if'
    for match in pattern.finditer(content):
        indent = match.group(1)
        replacement = f"{indent}return [^\n]+\n{indent}if"
        content = re.sub(pattern, replacement, content)
    
    return content


def fix_bare_except(content):
    """Fix bare except blocks by adding Exception."""
    # Pattern to match bare except:
    pattern = re.compile(r"(\s+)except:\s")
    
    # Replace with except Exception:
    for match in pattern.finditer(content):
        indent = match.group(1)
        content = content.replace(f"{indent}except:", f"{indent}except Exception:")
    
    return content


def process_file(file_path):
    """Process a single file to fix pylint issues."""
    print(f"Processing {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Apply fixes
    original_content = content
    content = fix_unused_imports(file_path, content)
    content = fix_unnecessary_pass(content)
    content = fix_unnecessary_elif_after_return(content)
    content = fix_bare_except(content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Fixed issues in {file_path}")
    else:
        print(f"  No issues to fix in {file_path}")


def process_directory(directory):
    """Recursively process Python files in a directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                process_file(file_path)


def main():
    """Main function to fix pylint issues in the codebase."""
    project_root = Path(__file__).parent.parent
    
    # Process each directory
    for directory in DIRECTORIES_TO_FIX:
        dir_path = project_root / directory
        if dir_path.exists():
            process_directory(dir_path)
    
    print("\nPylint issue fixing completed!")
    print("You may still need to manually fix some issues.")


if __name__ == "__main__":
    main()
