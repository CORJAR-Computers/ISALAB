import os
import re
import subprocess

def fix_f541():
    result = subprocess.run([r'.\.venv\Scripts\python.exe', '-m', 'flake8', '.', '--select=F541', '--exclude=.venv,__pycache__,alembic,build,dist,IsaLab-v1.0-win64.zip'], capture_output=True, text=True)
    
    for line in result.stdout.splitlines():
        if not line.strip() or 'F541' not in line:
            continue
        
        parts = line.split(':')
        if len(parts) >= 3:
            file_path = parts[0]
            line_num = int(parts[1]) - 1
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Simple replacement of the first f" or f' or f""" or f'''
            content = lines[line_num]
            # Replace f""" or f'''
            if 'f"""' in content:
                content = content.replace('f"""', '"""', 1)
            elif "f'''" in content:
                content = content.replace("f'''", "'''", 1)
            elif 'f"' in content:
                content = content.replace('f"', '"', 1)
            elif "f'" in content:
                content = content.replace("f'", "'", 1)
                
            lines[line_num] = content
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
if __name__ == "__main__":
    fix_f541()
