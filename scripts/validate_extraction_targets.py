"""
Validate that extraction targets exist in the source before any code generation.
Blocks generators from referencing non-existent functions/classes.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set


def extract_names_from_source(source_path: Path) -> Set[str]:
    """Parse source file and return all defined function, class, and module-level names."""
    with open(source_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)

    return names


def validate_extraction_targets(source_path: Path, target_names: Dict[str, List[str]]) -> bool:
    """
    Validate that all target names exist in the source.
    Returns False if ANY target name is missing.
    """
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        return False

    actual_names = extract_names_from_source(source_path)

    missing = {}
    for module, names in target_names.items():
        missing_names = [n for n in names if n not in actual_names]
        if missing_names:
            missing[module] = missing_names

    if missing:
        print(f"ERROR: Extraction targets missing from source ({source_path}):")
        for module, names in missing.items():
            print(f"  {module}: {', '.join(names)}")
        return False

    total_targets = sum(len(v) for v in target_names.values())
    print(f"OK: All {total_targets} target names validated against source")
    return True


# Known extraction targets — verified against real monolithic source (2026-08-14).
# Only lists names that exist in fungaiV2_extracted/fung_ai_v2.py.
# validators.py, environment.py, cache.py were new code added during extraction
# (not present in monolith) — those modules are not validated here.
ACTUAL_EXPORTS = {
    'ca_engine': ['CARule', 'step_ca', 'initialize_random', 'compute_density'],
    'fitness': [
        'has_path', 'evaluate_ca_rule', 'compute_descriptors',
        'compute_pattern_entropy', 'compute_pacing_variance',
        'compute_interestingness', 'classify_topology'
    ],
    'archive': ['GridArchive', 'ArchiveCell'],
    'emitters': ['Emitter', 'MAP_Elites_Emitter'],
    'algorithms': ['RandomSearch', 'Standard_MAP_Elites'],
    'exporters': ['GodotExporter'],
}


def main():
    source_path = Path(__file__).parent.parent / 'fungaiV2_extracted' / 'fung_ai_v2.py'

    if not source_path.exists():
        print(f"Using fallback source: fung_ai_v2.py in project root")
        source_path = Path(__file__).parent.parent / 'fung_ai_v2.py'

    success = validate_extraction_targets(source_path, ACTUAL_EXPORTS)

    if not success:
        print("\nVALIDATION FAILED: Do not run extraction generators.")
        return 1

    print("SAFE: Proceed with extraction.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
