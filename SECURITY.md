# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in the Fung Godot Toolkit (the
Godot addon under `godot_addon/`, the Python bridge under `bridge/`, or the
`fung_ai_v2` generation engine), please **do not** open a public GitHub
issue.

Instead, report it privately using GitHub's [private security advisory
tool](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
on this repository (**Security > Advisories > Report a vulnerability**).
This lets maintainers assess and fix the issue before it's publicly
disclosed.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (a minimal `request.json` or recipe config, if
  relevant).
- Which component is affected (Godot addon, bridge CLI, or the generation
  engine).

## Scope notes

This is an offline-first, local tool: the Python bridge is invoked as a
subprocess by the Godot editor and reads/writes files under a per-project
job directory. There is no network service or remote endpoint shipped as
part of the toolkit itself. Reports involving untrusted input to the
bridge (e.g. a malicious `request.json`, recipe file, or `TileSet`/scene
resource fed into the export path) are still in scope and appreciated.

## Response

There is no dedicated security contact or SLA established for this project
yet — reports will be triaged by the maintainers on a best-effort basis
through the private advisory process above.
