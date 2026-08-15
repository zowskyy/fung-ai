"""fung_ai_v2: Cellular Automaton Dungeon Generator v0.1.0

Game-design-aware Quality-Diversity cave generator using MAP-Elites.
Evolves Conway-Life-style CA rules into 2D cave/dungeon layouts and
exports results to Godot-4-compatible scenes.
"""
__version__ = "0.1.0"

from .ca_engine import CARule, initialize_random, step_ca
from .archive import GridArchive
from .exporters import GodotExporter
from .fitness import compute_descriptors, evaluate_ca_rule, has_path
from .validators import validate_cli_args, validate_grid, validate_rule_string

__all__ = [
    "__version__",
    # CA engine
    "CARule",
    "step_ca",
    "initialize_random",
    # Validators
    "validate_rule_string",
    "validate_grid",
    "validate_cli_args",
    # Fitness
    "has_path",
    "evaluate_ca_rule",
    "compute_descriptors",
    # Archive
    "GridArchive",
    # Exporters
    "GodotExporter",
]
