# Analysis

Understand the issue against the codebase before writing any code. The goal is a short, concrete plan the user can approve.

## Gather context

- Read the issue in full: description, acceptance criteria, the linked epic or issues, and the comments.
- Locate the affected code: search for the entities, endpoints, or components the issue names.
- Note the project's conventions: CONTRIBUTING, CLAUDE.md or AGENTS.md, lint config, and the `clean-code` standards for the detected stack.

## Investigate in parallel

For a non-trivial issue, dispatch parallel subagents, each on one facet, then synthesize:

- Current behaviour and where it lives.
- The change surface: files, modules, data model, API.
- Impact and risk: what else touches this, migrations, backward compatibility.
- Test surface: what needs covering.

## Produce the plan

Present a short plan:

- What changes, file by file at a high level.
- New or changed tests.
- Any dependency, migration, or config change. Dependencies get vetted before install.
- Open questions or assumptions.

Wait for the user's go before implementing. Do not expand scope beyond the issue without asking.
