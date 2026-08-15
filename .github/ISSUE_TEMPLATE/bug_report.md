---
name: Bug report
about: Report a problem with the Fung Godot Toolkit addon or bridge
title: "[Bug] "
labels: bug
assignees: ''
---

## Component

<!-- Where does this bug live? Delete the ones that don't apply. -->

- [ ] Godot addon (`godot_addon/addons/fung_godot/...`)
- [ ] Python bridge (`bridge/...`)
- [ ] Generation engine (`fung_ai_v2/...`)
- [ ] Documentation
- [ ] Other / not sure

## Describe the bug

A clear description of what went wrong.

## Steps to reproduce

1.
2.
3.

If this involves generation, please include:

- Recipe id used (`recipe_id`)
- Seed
- Map size (`map_size_tiles`)
- Generation budget (Fast / Balanced / Thorough)

If this involves the bridge directly, please include the relevant
`request.json` and, if generation failed, the `job.log` from the job
directory (`.fung/jobs/<request_id>/`).

## Expected behavior

What you expected to happen instead.

## Actual behavior

What actually happened. Include any error message from the Generate/
Export tab status labels, and the exact `code`/`message` from `result.json`
if the bridge returned an error (see `docs/bridge_protocol.md`).

## Environment

- Godot version:
- OS:
- Python version (`python3 --version`):
- Fung Godot Toolkit version (from `plugin.cfg`, currently `0.1.0`):
- How you're running Python (`FUNG_PYTHON` set? venv? system python?):

## Additional context

Logs, screenshots, or anything else relevant.
