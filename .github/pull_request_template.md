## Summary

<!-- What does this PR change, and why? -->

## Component(s) touched

- [ ] Godot addon (`godot_addon/addons/fung_godot/...`)
- [ ] Python bridge (`bridge/...`)
- [ ] Generation engine (`fung_ai_v2/...`)
- [ ] Recipes (`bridge/generation.py`'s `RECIPES`)
- [ ] Documentation (`docs/...`, `README`, etc.)
- [ ] CI / governance

## How was this verified?

This project's convention is a real, observed-passing gate before calling
work done — not just "I pushed the commit." Check what actually applies:

- [ ] `python3 -m pytest tests/ -q` passes locally
- [ ] `ruff check fung_ai_v2/ bridge/ scripts/ --select=E,W,F` passes locally
- [ ] GDScript changes: verified by the real `godot_addon.yml` CI run (no
      local Godot binary was available) — link the passing run
- [ ] GDScript changes: verified locally with a Godot 4.3 binary
- [ ] New/changed recipe: included a deterministic seed + expected metric
      ranges (per `.github/ISSUE_TEMPLATE/recipe_submission.md`) and
      confirmed the recipe actually produces candidates
- [ ] Docs-only change: no code paths affected

## Related issue(s)

<!-- Closes #... -->

## Additional notes

<!-- Anything a reviewer should know: known limitations, follow-ups, etc. -->
