import os
import re

directory = '.'

replacements = {
    'Club CRM': 'Club CRM',
    'APIIT Kandy Club CRM': 'APIIT Kandy Club CRM',
    'APIIT Kandy Club': 'APIIT Kandy Club',
    'Club Roles': 'Club Roles',
    'club roles': 'club roles',
    'Generic': 'Generic',
    'Standard theme': 'Standard theme',
    'standard palette (Slate, Blue, Amber)': 'standard palette (Slate, Blue, Amber)',
    'Amber Accent': 'Amber Accent',
    'Deep Slate': 'Deep Slate',
    'Bright Blue': 'Bright Blue',
    '#0f172a': '#0f172a',
    '#1e293b': '#1e293b',
    '#2563eb': '#2563eb',
    '#fbbf24': '#fbbf24',
    '#fbbf24': '#fbbf24',
    '#1d4ed8': '#1d4ed8',
    '--brand-primary': '--brand-primary',
    '--brand-secondary': '--brand-secondary',
    '--brand-accent': '--brand-accent'
}

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        # Case insensitive replace for some terms if needed, but here exact match is fine
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')

for root, dirs, files in os.walk(directory):
    if '.git' in root or 'venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith(('.md', '.html', '.css', '.py', '.sql')):
            filepath = os.path.join(root, file)
            replace_in_file(filepath)
