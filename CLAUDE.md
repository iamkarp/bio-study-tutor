# build-study-tutor — Skill Repo

This repository is the **`build-study-tutor` Claude Code skill** and a reference instance.

## Layout

- `skill/` — The Claude Code skill. Install it with `cp -r skill ~/.claude/skills/build-study-tutor/`.
- `examples/bio-1320/` — A complete working instance built for Biology 1320, Exam 3 (Chapters 9–13). Use it as a reference when building a tutor for a different subject.

## Working on the skill

To update the skill procedure, edit `skill/SKILL.md`.
To add or update templates, edit files in `skill/templates/`.
To update reference documentation Claude reads during the skill, edit files in `skill/reference/`.

## Working on the bio example

See `examples/bio-1320/CLAUDE.md` for the bio-specific schema (node types, edge relations, build pipeline).
