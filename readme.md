# AI Skills

A Claude Code plugin marketplace of [Agent Skills](https://agentskills.io/specification) that teach an AI assistant to write clean, idiomatic code and load only the guidance a task needs.

The repo hosts a marketplace that can hold several plugins. It ships one today, `clean-code`, and more can be added later without restructuring.

## Plugins

| Plugin | What it does |
|---|---|
| `clean-code` | Stack-aware clean-code best practices for frontend, backend, and shared engineering standards |

## The clean-code plugin

Three skills. Each is a `SKILL.md` router plus a set of `references/*.md` files. The router detects the project's stack and version, then reads only the matching reference, so the assistant never carries guidance for frameworks the project does not use.

| Skill | Use for | Covers |
|---|---|---|
| `frontend-development` | UI, components, styling, client state, a11y | Angular, React, Next.js, Vue, accessibility, CSS, component testing, client performance |
| `backend-development` | APIs, services, data access, auth | NestJS, Node.js, Java, Spring Boot, API design, database, auth/security, integration testing |
| `core-development` | The baseline shared by both | TypeScript, JavaScript, clean code, documentation, testing, git/gitflow, security, versioning |

Frontend and backend reference the core for anything cross-cutting. Nothing is duplicated across skills.

### How loading works

1. The router reads `package.json`, `pom.xml`, or `build.gradle` to detect the stack and its resolved version.
2. It reads the one framework reference that matches, and applies only the rules that fit the detected version.
3. It pulls in cross-cutting references (accessibility, testing, security, and so on) only when the task calls for them.

A React task loads the React reference and, if relevant, accessibility and testing. Angular, Vue, and every backend file stay on disk, unread.

## Install

### Claude Code (recommended)

```
/plugin marketplace add xItsSky/ai-skills
/plugin install clean-code@ai-skills
```

The first command registers the marketplace, the second installs the plugin and its three skills. Update later with `/plugin marketplace update ai-skills`.

### Other tools (manual)

The skills are plain Markdown and work with any tool that supports Agent Skills. Symlink them into the tool's skills directory:

```bash
ln -s "$PWD/clean-code/skills/frontend-development" ~/.claude/skills/frontend-development
ln -s "$PWD/clean-code/skills/backend-development"  ~/.claude/skills/backend-development
ln -s "$PWD/clean-code/skills/core-development"     ~/.claude/skills/core-development
```

Codex uses `~/.agents/skills/`. Copilot CLI and Gemini CLI auto-discover installed skills.

## Layout

```
.claude-plugin/marketplace.json      Marketplace catalog
clean-code/
  .claude-plugin/plugin.json         Plugin manifest
  skills/
    frontend-development/  SKILL.md + references/*.md
    backend-development/   SKILL.md + references/*.md
    core-development/      SKILL.md + references/*.md
```

## Extending

**Add a stack to an existing skill:** drop a new `references/<stack>.md` into the right skill, matching the format of the existing references, and add one row to the detection table in that skill's `SKILL.md`.

**Add a new plugin to the marketplace:** create a sibling folder with its own `.claude-plugin/plugin.json` and `skills/`, then add one entry to the `plugins` array in `.claude-plugin/marketplace.json`.
