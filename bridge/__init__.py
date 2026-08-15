"""bridge: Local JSON file protocol for Godot ↔ Python generation requests.

v0.1 implementation uses atomic JSON writes in .fung/jobs/ directories.
Godot writes request.json, Python processes it, writes status.json and result.json.
"""
__version__ = "0.1.0"
