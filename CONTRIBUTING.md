# Contributing

Thanks for helping improve these skills. The repo is a Claude Code and Codex plugin marketplace built from shared Markdown skills, so most contributions are edits to reference files.

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

1. Create a sibling folder with `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and one shared `skills/` directory. Copy the metadata structure from an existing plugin.
2. Add an entry to `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. Use the same plugin name and repository-relative source directory in both. Codex entries use a local source object, an installation/authentication policy, and a category.
3. Keep the version identical in both plugin manifests and the Claude catalog entry. Bump it when shipped plugin content changes so installed caches can pick up the update.
4. Put `name` and `description` in every skill's YAML frontmatter. Quote or fold descriptions containing trigger examples with `#`; quote descriptions containing YAML-sensitive punctuation such as `: `.

Resolve reference paths from the installed skill directory, never from a tool-specific cache location. Keep related skills in the same plugin when they depend on sibling references. Document dependencies on other plugins and external tools; a marketplace entry does not install them automatically.

## Validate before opening a PR

Run the same validation and regression tests as CI (Python 3.12+):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r .github/requirements-validation.txt
.venv/bin/python .github/scripts/validate_skills.py
.venv/bin/python -m coverage run --source=.github/scripts -m unittest discover -s .github/scripts/tests
.venv/bin/python -m coverage report --omit='*/tests/*' --fail-under=80
```

The validator checks both catalogs, matching plugin names and versions, local source paths, shared skill directories, and YAML metadata. Regression tests exercise malformed catalogs, missing files, and descriptions truncated by YAML comments. These checks cover this repository's packaging conventions; they do not replace installation tests or validate every possible upstream manifest field.

With Claude Code installed, also run `claude plugin validate .` and `claude plugin validate <plugin-directory>` for each changed plugin.

Before shipping packaging changes, register the local repository root in separate test configurations for Claude Code and Codex, install all five plugins, and verify that the installed packages contain all seven skills and their references. Start fresh conversations to check discovery and representative prompts when an authenticated runtime is available. Record the CLI versions and any untested runtime behavior in the PR.

## Git workflow

- Branch from `main`. Never commit to `main` directly. Naming: `feat/<desc>`, `fix/<desc>`, `chore/<desc>`, `docs/<desc>`, or `feat/#<issue>-<desc>`.
- Conventional Commits: `<type>(<scope>): <description>`, imperative, lowercase, under 72 characters. One concern per commit.
- Open a PR against `main`, fill in the template, and link the issue.
