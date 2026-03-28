import os
import re

directory = r"c:\Helm\FossHack\TOBU\backend\search_and_index"
# Fix imports starting with from .
# and from .module

files = [f for f in os.listdir(directory) if f.endswith(".py")]

for filename in files:
    filepath = os.path.join(directory, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # from .module import 
    new_content = re.sub(r"from \.(\w+)", r"from backend.search_and_index.\1", content)
    # from . import (or just from . import module)
    new_content = re.sub(r"from \. ", r"from backend.search_and_index ", new_content)
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed imports in {filename}")
