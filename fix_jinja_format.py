import re
import os

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix {% ... %}
    # Matches:
    # {
    #     % include 'styles/base.css' %
    # }
    content = re.sub(r'\{\s*(%[^%]+%)\s*\}', r'{{\1}}', content)
    # The above regex will capture `% include 'styles/base.css' %` in \1. 
    # Oh wait, Jinja syntax is `{% ... %}` not `{{% ... %}}`. So it should be `{\1}`.
    content = re.sub(r'\{\s*(%[^%]+%)\s*\}', r'{\1}', content)

    # Fix {{ ... }}
    # Matches:
    # {
    #     {
    #         variable
    #     }
    # }
    content = re.sub(r'\{\s*\{\s*([^{}]+?)\s*\}\s*\}', r'{{\1}}', content)

    # Fix dangling semi-colons
    # Example: {{ config.marca_agua_opacidad }} \n\n ; -> {{ config.marca_agua_opacidad }};
    content = re.sub(r'(\}\})\s*;', r'\1;', content)

    # Fix multiple `mm` in base_report.html
    # margin: 35mm {{ margenes.derecho }} \n\n mm {{ margenes.inferior }} \n\n mm ...
    content = re.sub(r'(\}\})\s*mm', r'\1mm', content)

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
