#!/usr/bin/env python3
"""Comprehensive codebase analysis script."""
import os
from pathlib import Path
from collections import defaultdict
import json

def count_lines_and_files(root_dir, exclude_dirs={'.git', '__pycache__', '.venv', 'venv', 'build', 'node_modules', '.pytest_cache', 'dist'}):
    stats = defaultdict(lambda: {'files': 0, 'lines': 0, 'file_list': []})
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = Path(filename).suffix.lower()
            
            if not ext:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    stats[ext]['files'] += 1
                    stats[ext]['lines'] += lines
                    rel_path = os.path.relpath(filepath, root_dir)
                    stats[ext]['file_list'].append({'path': rel_path, 'lines': lines})
            except:
                pass
    
    return stats

def analyze_by_directory(root_dir, exclude_dirs={'.git', '__pycache__', '.venv', 'venv', 'build', 'node_modules', '.pytest_cache', 'dist'}):
    """Analyze code distribution by major directory."""
    dir_stats = defaultdict(lambda: {'files': 0, 'lines': 0, 'py_files': 0, 'py_lines': 0})
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = Path(filename).suffix.lower()
            
            if not ext:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    
                    # Get the top-level directory
                    rel_path = os.path.relpath(filepath, root_dir)
                    top_dir = rel_path.split(os.sep)[0]
                    
                    dir_stats[top_dir]['files'] += 1
                    dir_stats[top_dir]['lines'] += lines
                    
                    if ext == '.py':
                        dir_stats[top_dir]['py_files'] += 1
                        dir_stats[top_dir]['py_lines'] += lines
            except:
                pass
    
    return dir_stats

def find_large_files(root_dir, min_lines=500, exclude_dirs={'.git', '__pycache__', '.venv', 'venv', 'build', 'node_modules', '.pytest_cache', 'dist'}):
    """Find files larger than min_lines."""
    large_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = Path(filename).suffix.lower()
            
            if ext not in ['.py', '.js', '.ts', '.tsx']:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    if lines >= min_lines:
                        rel_path = os.path.relpath(filepath, root_dir)
                        large_files.append({'path': rel_path, 'lines': lines, 'ext': ext})
            except:
                pass
    
    return sorted(large_files, key=lambda x: x['lines'], reverse=True)

# Run analysis
print("=" * 100)
print("CODE METRICS BY FILE TYPE")
print("=" * 100)

stats = count_lines_and_files('.')
print(f"{'Extension':<15} {'Files':>10} {'Lines':>15} {'Avg Lines/File':>15}")
print("-" * 100)

total_files = 0
total_lines = 0
for ext in sorted(stats.keys(), key=lambda x: stats[x]['lines'], reverse=True):
    s = stats[ext]
    avg = s['lines'] // s['files'] if s['files'] > 0 else 0
    print(f"{ext:<15} {s['files']:>10} {s['lines']:>15,} {avg:>15}")
    total_files += s['files']
    total_lines += s['lines']

print("-" * 100)
print(f"{'TOTAL':<15} {total_files:>10} {total_lines:>15,}")
print("=" * 100)
print()

# By directory
print("=" * 100)
print("CODE DISTRIBUTION BY DIRECTORY")
print("=" * 100)
dir_stats = analyze_by_directory('.')
print(f"{'Directory':<25} {'Files':>10} {'Lines':>15} {'Python Files':>15} {'Python Lines':>15}")
print("-" * 100)

total_py_files = 0
total_py_lines = 0
for dirname in sorted(dir_stats.keys()):
    d = dir_stats[dirname]
    print(f"{dirname:<25} {d['files']:>10} {d['lines']:>15,} {d['py_files']:>15} {d['py_lines']:>15,}")
    total_py_files += d['py_files']
    total_py_lines += d['py_lines']

print("-" * 100)
print(f"{'TOTAL':<25} {sum(d['files'] for d in dir_stats.values()):>10} {sum(d['lines'] for d in dir_stats.values()):>15,} {total_py_files:>15} {total_py_lines:>15,}")
print("=" * 100)
print()

# Large files
print("=" * 100)
print("LARGEST CODE FILES (Python/JavaScript/TypeScript, 500+ lines)")
print("=" * 100)
large_files = find_large_files('.', min_lines=500)
print(f"{'Path':<60} {'Lines':>10} {'Type':>10}")
print("-" * 100)
for f in large_files[:30]:
    print(f"{f['path']:<60} {f['lines']:>10} {f['ext']:>10}")
print("=" * 100)
print()

# Python-specific analysis
print("=" * 100)
print("PYTHON CODEBASE ANALYSIS")
print("=" * 100)
py_stats = stats['.py'] if '.py' in stats else {'files': 0, 'lines': 0, 'file_list': []}
print(f"Total Python Files: {py_stats['files']}")
print(f"Total Python Lines: {py_stats['lines']:,}")
print(f"Average Lines per Python File: {py_stats['lines'] // py_stats['files'] if py_stats['files'] > 0 else 0}")
print()

# Categorize Python files by directory
py_by_dir = defaultdict(lambda: {'count': 0, 'lines': 0})
for file_info in py_stats['file_list']:
    path = file_info['path']
    parts = path.split(os.sep)
    if len(parts) > 1:
        category = parts[0]
    else:
        category = 'root'
    py_by_dir[category]['count'] += 1
    py_by_dir[category]['lines'] += file_info['lines']

print(f"{'Python Category':<25} {'Files':>10} {'Lines':>15} {'Avg Lines':>15}")
print("-" * 100)
for cat in sorted(py_by_dir.keys()):
    info = py_by_dir[cat]
    avg = info['lines'] // info['count'] if info['count'] > 0 else 0
    print(f"{cat:<25} {info['count']:>10} {info['lines']:>15,} {avg:>15}")
print("=" * 100)
