import re
import os

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix {{% ... %}} -> {% ... %}
    content = re.sub(r'\{\{%\s*', r'{% ', content)
    content = re.sub(r'\s*%\}\}', r' %}', content)

    # In base_report.html: `size: {{config.tipo_papel | default('a4')}};`
    # and `margin: 35mm {{margenes.derecho | default(15)}}mm ...`

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
