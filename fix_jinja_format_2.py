import re
import os

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix {% ... %}
    content = re.sub(r'\{\s*(%[^%]+%)\s*\}', r'{\1}', content)

    # Fix {{ ... }}
    content = re.sub(r'\{\s*\{\s*([^{}]+?)\s*\}\s*\}', r'{{\1}}', content)

    # Fix dangling characters after jinja tag
    # Example: {{ variable }} \n\n ; -> {{ variable }};
    # Example: {{ variable }} \n\n pt; -> {{ variable }}pt;
    # We will just remove any whitespace between `}}` and a following `;`, `pt`, `mm`, `px` etc.
    content = re.sub(r'(\}\})\s+;', r'\1;', content)
    content = re.sub(r'(\}\})\s+pt', r'\1pt', content)
    content = re.sub(r'(\}\})\s+mm', r'\1mm', content)
    content = re.sub(r'(\}\})\s+px', r'\1px', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    templates_dir = r'c:\ISALAB\templates'
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html') or file.endswith('.css'):
                filepath = os.path.join(root, file)
                print(f"Fixing {filepath}")
                fix_file(filepath)

if __name__ == '__main__':
    main()
