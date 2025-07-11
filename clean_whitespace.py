#!/usr/bin/env python3
"""
Script to clean whitespace issues in Python files for CI compliance.
"""

import os
import re

def clean_whitespace_in_file(filepath):
    """Clean trailing whitespace and blank lines with whitespace."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.splitlines()
    cleaned_lines = [line.rstrip() for line in lines]
    
    cleaned_content = '\n'.join(cleaned_lines)
    if content.endswith('\n'):
        cleaned_content += '\n'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f'Cleaned whitespace in {filepath}')

def main():
    """Clean all Python files in the project."""
    for root, dirs, files in os.walk('job_instruction_downloader'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                clean_whitespace_in_file(filepath)

if __name__ == '__main__':
    main()
