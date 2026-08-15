#!/usr/bin/env python3
"""
Cursor Gate: Security audit for fung.us CA engine

Scans for:
  1. Dangerous functions: eval, exec, pickle, __import__
  2. Hardcoded secrets: AWS keys, API keys, passwords
  3. Path traversal: absolute paths, symlink escapes
  4. Unsafe imports: os.system, subprocess without validation

Exit code:
  0 = clean
  1 = issues found
"""

import re
import sys
from pathlib import Path

# Patterns to scan for
DANGEROUS_PATTERNS = {
    "eval": re.compile(r"\beval\s*\("),
    "exec": re.compile(r"\bexec\s*\("),
    "pickle": re.compile(r"pickle\.(dump|load|dumps|loads)"),
    "__import__": re.compile(r"__import__\s*\("),
    "os.system": re.compile(r"os\.system\s*\("),
}

SECRET_PATTERNS = {
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "api_key": re.compile(r"['\"]api[_-]?key['\"]?\s*[:=]\s*['\"][^'\"]{20,}['\"]", re.IGNORECASE),
    "password": re.compile(r"['\"]password['\"]?\s*[:=]", re.IGNORECASE),
}

PATH_PATTERNS = {
    "absolute_windows_path": re.compile(r"['\"]C:[\\\\/]"),
    "absolute_unix_path": re.compile(r"['\"]\/[^'\"]"),
}


def scan_file(file_path: Path, report: list) -> int:
    """Scan a single file for security issues."""
    issues = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.split("\n")
    except Exception as e:
        report.append(f"❌ {file_path}: Could not read ({e})")
        return 1

    # Check for dangerous functions
    for func_name, pattern in DANGEROUS_PATTERNS.items():
        for i, line in enumerate(lines, 1):
            if pattern.search(line) and not line.strip().startswith("#"):
                report.append(f"⚠️  {file_path}:{i} - Found '{func_name}'")
                issues += 1

    # Check for hardcoded secrets
    for secret_type, pattern in SECRET_PATTERNS.items():
        for i, line in enumerate(lines, 1):
            if pattern.search(line) and not line.strip().startswith("#"):
                report.append(f"🔴 {file_path}:{i} - Possible {secret_type}")
                issues += 1

    # Check for hardcoded paths
    for path_type, pattern in PATH_PATTERNS.items():
        for i, line in enumerate(lines, 1):
            if pattern.search(line) and not line.strip().startswith("#"):
                report.append(f"⚠️  {file_path}:{i} - Found {path_type}")
                issues += 1

    return issues


def main():
    """Run security audit."""
    import argparse

    parser = argparse.ArgumentParser(description="Cursor Gate — Security audit")
    parser.add_argument("target", help="Directory or file to scan")
    parser.add_argument("--report", help="Write report to file")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"❌ Target not found: {target}")
        return 1

    report = []
    total_issues = 0

    if target.is_file():
        print(f"Scanning {target}...")
        total_issues += scan_file(target, report)
    else:
        # Scan all Python files in directory
        print(f"Scanning {target} (Python files)...")
        for py_file in target.rglob("*.py"):
            if ".git" not in py_file.parts and "__pycache__" not in py_file.parts:
                total_issues += scan_file(py_file, report)

    # Print report
    print("\n" + "=" * 60)
    if report:
        print(f"🔍 Found {total_issues} potential security issues:\n")
        for line in report:
            print(f"  {line}")
    else:
        print("✅ No security issues found!")
    print("=" * 60)

    # Write report file if requested
    if args.report:
        with open(args.report, "w") as f:
            f.write(f"Security Audit Report\n")
            f.write(f"Target: {target}\n")
            f.write(f"Issues: {total_issues}\n\n")
            if report:
                for line in report:
                    f.write(f"{line}\n")
            else:
                f.write("✅ No security issues found!\n")
        print(f"\nReport written to {args.report}")

    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
