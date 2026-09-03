# Contributing

Thanks for helping improve these skills. The repo is a Claude Code plugin marketplace built from plain Markdown, so most contributions are edits to reference files.

## Ground rules for reference content

Every `references/*.md` file follows the same shape. Match it.

- English only. No emoji, no em dashes, no filler or hype. Direct and declarative.
- Short sections, imperative bullets, fenced code blocks, and a final Do/Instead-of or Quick reference table.
- Best practices only. Assume a competent developer. No tutorials or history.
- Label version-specific rules with the version they apply to, for example `(React 19+)`. State what to do on a supported older version when it differs. Do not invent version numbers.

## Add a stack to an existing skill

1. Create `clean-code/skills/<skill>/references/<stack>.md`, matching an existing file.
2. Add one row to the detection table in that skill's `SKILL.md`.

## Add a new plugin to the marketplace

1. Create a sibling folder with `.claude-plugin/plugin.json` and a `skills/` directory.
2. Add one entry to the `plugins` array in `.claude-plugin/marketplace.json`.

## Validate before opening a PR

```bash
claude plugin validate .
```

Or run the same checks the CI runs, which need no Claude CLI:

```bash
pip install pyyaml
python .github/scripts/validate_skills.py
```

Both confirm the JSON manifests parse and every `SKILL.md` has valid frontmatter with a `name` and `description`.

## Git workflow

- Branch from `main`. Never commit to `main` directly. Naming: `feat/<desc>`, `fix/<desc>`, `chore/<desc>`, `docs/<desc>`, or `feat/#<issue>-<desc>`.
- Conventional Commits: `<type>(<scope>): <description>`, imperative, lowercase, under 72 characters. One concern per commit.
- Open a PR against `main`, fill in the template, and link the issue.
