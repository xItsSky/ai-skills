# AI Skills

[![Validate](https://github.com/xItsSky/ai-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/xItsSky/ai-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-6C5CE7)](https://docs.claude.com/en/docs/claude-code)

A marketplace of [Agent Skills](https://agentskills.io/specification) for application development. It gathers practical, reusable skills that teach an AI assistant how to build software well, packaged so you install them with a command instead of copying files.

The collection is built to grow. Each theme ships as its own plugin. Four are available today: `clean-code`, `code-review`, `epic-planning`, and `devops`.

## Install

```
/plugin marketplace add xItsSky/ai-skills
/plugin install clean-code@ai-skills
```

The first command registers the marketplace, the second installs a plugin and its skills. Update later with `/plugin marketplace update ai-skills`. Using another tool or prefer a manual setup? See [Manual install](#manual-install).

## What's inside

| Plugin | Skills | Focus |
|---|---|---|
| `clean-code` | `frontend-development`, `backend-development`, `core-development` | Stack-aware clean-code practices with progressive, token-lean loading |
| `code-review` | `review-changes` | Source-agnostic first-pass code review, reported as Conventional Comments |
| `epic-planning` | `plan-epic` | Feature idea to a complete epic and its stories on GitHub, Jira, or Trello |
| `devops` | `deployment` | Kubernetes and OpenShift deployment best practices, platform-detected |

More plugins will land here over time.

## clean-code

Three skills. Each is a `SKILL.md` router plus a set of `references/*.md` files. The router detects the project's stack and version, then reads only the reference that matches, so the assistant never carries guidance for frameworks the project does not use.

| Skill | Use for | Covers |
|---|---|---|
| `frontend-development` | UI, components, styling, client state, a11y | Angular, React, Next.js, Vue, accessibility, CSS, component testing, client performance |
| `backend-development` | APIs, services, data access, auth | NestJS, Node.js, Java, Spring Boot, API design, database, auth/security, integration testing |
| `core-development` | The baseline shared by both | TypeScript, JavaScript, clean code, architecture, NX, documentation, testing, git/gitflow, security, versioning |

Frontend and backend defer to the core for anything cross-cutting. Nothing is duplicated across skills.

### How the loading stays lean

1. The router reads `package.json`, `pom.xml`, or `build.gradle` to detect the stack and its resolved version.
2. It reads the one framework reference that matches, and applies only the rules that fit the detected version.
3. It pulls in cross-cutting references (accessibility, testing, security, and the like) only when the task calls for them.

Measured on install, about 330 tokens sit always-on: the three short skill descriptions. Router bodies and reference files load only when a skill fires and the task needs them. A React task pulls the React reference, plus accessibility and testing when relevant. Angular, Vue, and the entire backend stay on disk, unread.

## code-review

One skill, `review-changes`. A first-pass review of a change set, run across parallel dimensions and reported as [Conventional Comments](https://conventionalcomments.org/). It never approves or merges.

- **Sources:** a local working-tree diff, a branch against its base, or a GitHub or GitLab pull or merge request.
- **Dimensions:** correctness, security (with a dependency audit), architecture, tests, performance, readability, documentation, and an optional runtime pass. The set scales to the size of the change.
- **Output:** a local report by default, or inline comments when the target is a pull or merge request and the platform CLI is available.

When `clean-code` is installed, the review borrows its stack references as the standard to check against.

```
/plugin install code-review@ai-skills
```

## epic-planning

One skill, `plan-epic`. It turns a feature idea into a complete epic and its stories, then creates them on your tracker. The conversation is demanding by design: it challenges the idea until the business rules and edge cases are pinned down.

- **Flow:** challenge-driven discovery, a drafted epic with business rules front and centre, stories with their relations and estimates, grooming with or without you, optional sprint placement, and a dry-run preview before anything is created.
- **Trackers:** GitHub, Jira, Trello. The tracker is taken from a parameter, detected from context, or asked. Only the matching adapter loads.
- **Relations:** parent/child, needs, depends-on, blocks, and relates-to, mapped to each tracker's native links.

Nothing is created without your approval, and the final call on every choice is yours.

```
/plugin install epic-planning@ai-skills
```

## devops

One skill, `deployment`. Production best practices for shipping to Kubernetes and OpenShift. It detects the platform and loads only the matching manifest guidance.

- **Platforms:** Kubernetes as the baseline, plus an OpenShift delta (Routes, security context constraints, DeploymentConfig, builds, the `oc` workflow).
- **Covers:** resource requests and limits, probes, rollout strategy, pod disruption budgets, hardened security context, secrets, RBAC least privilege, and high availability.

```
/plugin install devops@ai-skills
```

## Layout

```
.claude-plugin/marketplace.json      Marketplace catalog
clean-code/
  .claude-plugin/plugin.json         Plugin manifest
  skills/
    frontend-development/  SKILL.md + references/
    backend-development/   SKILL.md + references/
    core-development/       SKILL.md + references/
code-review/
  .claude-plugin/plugin.json
  skills/
    review-changes/        SKILL.md + references/
epic-planning/
  .claude-plugin/plugin.json
  skills/
    plan-epic/             SKILL.md + references/ (+ platforms/)
devops/
  .claude-plugin/plugin.json
  skills/
    deployment/            SKILL.md + references/
```

## Manual install

The skills are plain Markdown and work with any tool that supports Agent Skills. Symlink them into the tool's skills directory:

```bash
ln -s "$PWD/clean-code/skills/frontend-development" ~/.claude/skills/frontend-development
ln -s "$PWD/clean-code/skills/backend-development"  ~/.claude/skills/backend-development
ln -s "$PWD/clean-code/skills/core-development"     ~/.claude/skills/core-development
```

Codex uses `~/.agents/skills/`. Copilot CLI and Gemini CLI auto-discover installed skills.

## Extending

**Add a stack to a skill:** drop a new `references/<stack>.md` into the right skill and add a row to the detection table in its `SKILL.md`.

**Add a new plugin:** create a sibling folder with its own `.claude-plugin/plugin.json` and `skills/`, then add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide and the house style.

## License

[MIT](LICENSE).
