"""Pure-Python static structural checker for GDScript files.

Godot 4.x is unavailable in this sandbox, so nothing here has ever been
parsed or run by the engine. This is not a real GDScript parser -- it only
catches mechanical mistakes that are cheap and reliable to check without one.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
SCAN_DIRS = [
    ROOT / "godot_addon" / "fung_core",
    ROOT / "examples" / "cave_boss",
    ROOT / "tools",
    # Fung Godot Toolkit (v0.1) addon - separate project sharing this checker
    # since the mechanical checks (bracket balance, naming, signal.emit
    # matching) are generic, not fung_core-specific.
    REPO_ROOT / "godot_addon" / "addons" / "fung_godot",
    REPO_ROOT / "godot_addon" / "tests",
    # v0.1 sample projects demonstrating the addon in a playable context.
    REPO_ROOT / "godot_addon" / "samples",
]

DELIMITER_PAIRS = {")": "(", "}": "{", "]": "["}
OPENERS = set(DELIMITER_PAIRS.values())
CLOSERS = set(DELIMITER_PAIRS.keys())

# Deliberate departures from strict PascalCase -> snake_case filenames,
# each a naming choice made when the file was written (dropping the "Fung"
# namespace prefix; matching Godot's own "TileMap" node capitalization)
# rather than a mistake worth flagging on every lint run.
NAME_EXCEPTIONS = {
    "FungLogger": "logger",
    "FungProjectSettings": "project_settings",
    "TileMapBuilder": "tilemap_builder",
}

CLASS_NAME_RE = re.compile(r"^class_name\s+(\w+)")
EXTENDS_RE = re.compile(r"^extends\s+(\w+)")
SIGNAL_RE = re.compile(r"^signal\s+(\w+)\s*\(")
# Matches "identifier.emit(" or "identifier.emit.call_deferred(", the two
# call shapes used in this codebase.
EMIT_RE = re.compile(r"(?<![.\w])(\w+)\.emit(?:\.call_deferred)?\s*\(")


def find_gd_files() -> list[Path]:
    files = []
    for directory in SCAN_DIRS:
        if directory.is_dir():
            files.extend(sorted(directory.rglob("*.gd")))
    return files


def strip_strings_and_comments(line: str) -> str:
    """Blank out string literals and trailing line comments so delimiter
    and identifier scans never see characters inside them."""
    result = []
    in_string = None
    i = 0
    length = len(line)
    while i < length:
        ch = line[i]
        if in_string:
            if ch == "\\" and i + 1 < length:
                result.append("  ")
                i += 2
                continue
            if ch == in_string:
                in_string = None
                result.append(" ")
                i += 1
                continue
            result.append(" ")
            i += 1
            continue
        if ch in ("'", '"'):
            in_string = ch
            result.append(" ")
            i += 1
            continue
        if ch == "#":
            result.append(" " * (length - i))
            break
        result.append(ch)
        i += 1
    return "".join(result)


def check_brackets(path: Path, lines: list[str]) -> list[tuple[Path, int, str]]:
    findings = []
    stack: list[tuple[int, str]] = []
    for lineno, raw_line in enumerate(lines, start=1):
        clean = strip_strings_and_comments(raw_line)
        for ch in clean:
            if ch in OPENERS:
                stack.append((lineno, ch))
            elif ch in CLOSERS:
                expected = DELIMITER_PAIRS[ch]
                if not stack:
                    findings.append((path, lineno, f"unmatched closing '{ch}' with no matching opener"))
                elif stack[-1][1] != expected:
                    open_line, open_ch = stack.pop()
                    findings.append(
                        (path, lineno, f"closing '{ch}' does not match '{open_ch}' opened on line {open_line}")
                    )
                else:
                    stack.pop()
    for open_line, open_ch in stack:
        findings.append((path, open_line, f"unclosed '{open_ch}' never closed"))
    return findings


def pascal_to_snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return s.lower()


def check_naming(path: Path, lines: list[str], class_names: dict[str, Path]) -> list[tuple[Path, int, str]]:
    findings = []
    class_name = None
    class_name_line = 0
    has_extends = False
    for lineno, raw_line in enumerate(lines, start=1):
        clean = strip_strings_and_comments(raw_line)
        if class_name is None:
            match = CLASS_NAME_RE.match(clean)
            if match:
                class_name = match.group(1)
                class_name_line = lineno
        if not has_extends and EXTENDS_RE.match(clean):
            has_extends = True

    if class_name is None:
        return findings

    if not has_extends:
        findings.append((path, class_name_line, f"class_name '{class_name}' has no matching 'extends' line"))

    expected_basename = NAME_EXCEPTIONS.get(class_name, pascal_to_snake(class_name))
    actual_basename = path.stem
    if expected_basename != actual_basename:
        findings.append(
            (
                path,
                class_name_line,
                f"class_name '{class_name}' converts to '{expected_basename}', "
                f"but file is named '{actual_basename}.gd'",
            )
        )

    if class_name in class_names:
        # Duplicate reporting happens once findings for all files are collected.
        pass
    class_names.setdefault(class_name, []).append((path, class_name_line))

    return findings


def check_indentation(path: Path, lines: list[str]) -> list[tuple[Path, int, str]]:
    findings = []
    codebase_style = None
    for lineno, raw_line in enumerate(lines, start=1):
        leading = raw_line[: len(raw_line) - len(raw_line.lstrip(" \t"))]
        if not leading:
            continue
        has_tab = "\t" in leading
        has_space = " " in leading
        if has_tab and has_space:
            findings.append((path, lineno, "line mixes tabs and spaces in leading whitespace"))
            continue
        if codebase_style is None:
            codebase_style = "tab" if has_tab else "space"
        elif codebase_style == "tab" and has_space:
            findings.append((path, lineno, "line uses space indentation; rest of file uses tabs"))
        elif codebase_style == "space" and has_tab:
            findings.append((path, lineno, "line uses tab indentation; rest of file uses spaces"))
    return findings


def check_signals(path: Path, lines: list[str]) -> list[tuple[Path, int, str]]:
    findings = []
    signal_names = set()
    for raw_line in lines:
        clean = strip_strings_and_comments(raw_line)
        match = SIGNAL_RE.match(clean.strip())
        if match:
            signal_names.add(match.group(1))

    if not signal_names:
        return findings

    for lineno, raw_line in enumerate(lines, start=1):
        clean = strip_strings_and_comments(raw_line)
        for match in EMIT_RE.finditer(clean):
            identifier = match.group(1)
            if identifier not in signal_names:
                findings.append(
                    (path, lineno, f"'{identifier}.emit(...)' does not match any signal declared in this file")
                )
    return findings


def main() -> int:
    files = find_gd_files()
    findings_by_category: dict[str, list[tuple[Path, int, str]]] = {
        "BRACKETS": [],
        "NAMING": [],
        "DUPLICATE": [],
        "INDENT": [],
        "SIGNAL": [],
    }
    class_names: dict[str, list[tuple[Path, int]]] = {}

    for path in files:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        findings_by_category["BRACKETS"].extend(check_brackets(path, lines))
        findings_by_category["NAMING"].extend(check_naming(path, lines, class_names))
        findings_by_category["INDENT"].extend(check_indentation(path, lines))
        findings_by_category["SIGNAL"].extend(check_signals(path, lines))

    for class_name, occurrences in class_names.items():
        if len(occurrences) > 1:
            for path, lineno in occurrences:
                others = ", ".join(str(p.relative_to(REPO_ROOT)) for p, _ in occurrences if p != path)
                findings_by_category["DUPLICATE"].append(
                    (path, lineno, f"class_name '{class_name}' also declared in: {others}")
                )

    findings_by_file: dict[Path, list[tuple[str, int, str]]] = {}
    total_findings = 0
    for category, findings in findings_by_category.items():
        for path, lineno, message in findings:
            findings_by_file.setdefault(path, []).append((category, lineno, message))
            total_findings += 1

    for path in sorted(findings_by_file):
        rel_path = path.relative_to(REPO_ROOT)
        entries = sorted(findings_by_file[path], key=lambda entry: entry[1])
        for category, lineno, message in entries:
            print(f"[{category}] {rel_path}:{lineno}: {message}")

    print(f"\nScanned {len(files)} files, {total_findings} findings.")
    return 0 if total_findings == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
