# AI Skills

[![Validate](https://github.com/xItsSky/ai-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/xItsSky/ai-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-6C5CE7)](https://docs.claude.com/en/docs/claude-code)

A marketplace of [Agent Skills](https://agentskills.io/specification) for application development. It gathers practical, reusable skills that teach an AI assistant how to build software well, packaged so you install them with a command instead of copying files.

The collection is built to grow. Each theme ships as its own plugin. Five are available today: `clean-code`, `code-review`, `epic-planning`, `devops`, and `issue-delivery`.

## Install

### Claude Code

```
/plugin marketplace add xItsSky/ai-skills
/plugin install clean-code@ai-skills
```

The first command registers the marketplace; the second installs a plugin and its skills. Update the catalog with `/plugin marketplace update ai-skills`.

### Codex

Use a Codex CLI with `codex plugin` support. Local marketplace installation was tested with version `0.154.0`:

```bash
codex plugin marketplace add xItsSky/ai-skills
codex plugin add clean-code@ai-skills
codex plugin add code-review@ai-skills
codex plugin add epic-planning@ai-skills
codex plugin add devops@ai-skills
codex plugin add issue-delivery@ai-skills
```

Install only the plugins you need. `issue-delivery` requires `clean-code`; its optional self-review uses `code-review`. Keep all three skills in the `clean-code` plugin together because they share references.

Check the installation with `codex plugin list --marketplace ai-skills --json`. Start a new Codex conversation to use the installed skills. For example, ask it to review your changes or apply the coding standards for your project.

To update, refresh the catalog and install the desired plugins again:

```bash
codex plugin marketplace upgrade ai-skills
codex plugin add clean-code@ai-skills
```

Repeat the second command for each installed plugin you want to update, then start a new conversation. For a local checkout, register its root with `codex plugin marketplace add /absolute/path/to/ai-skills`.

Both tools load the same `skills/` files. Each has its own catalog and manifest metadata. If your Codex version has no `plugin` command, use [manual installation](#manual-install) or update Codex.

### Runtime prerequisites

Installing a skill does not install or authenticate external tools. Tracker workflows need the corresponding access: `gh` for GitHub, `glab` for GitLab, an available Jira CLI/MCP/API connection, or Trello API credentials. Deployment tasks need the relevant project tools and cluster access when running commands.

Review and issue analysis use subagents when available and perform the same passes sequentially otherwise. Existing approval requirements for tracker changes and implementation still apply.

## What's inside

| Plugin | Skills | Focus |
|---|---|---|
| `clean-code` | `frontend-development`, `backend-development`, `core-development` | Stack-aware clean-code practices with progressive, token-lean loading |
| `code-review` | `review-changes` | Source-agnostic first-pass code review, reported as Conventional Comments |
| `epic-planning` | `plan-epic` | Feature idea to a complete epic and its stories on GitHub, Jira, or Trello |
| `devops` | `deployment` | Kubernetes and OpenShift deployment best practices, platform-detected |
| `issue-delivery` | `deliver-issue` | Take an issue to an open pull request on GitHub, GitLab, or Jira |

More plugins will land here over time.

## clean-code

Three skills. Each is a `SKILL.md` router plus a set of `references/*.md` files. The router detects the project's stack and version, then reads only the reference that matches, so the assistant never carries guidance for frameworks the project does not use.

| Skill | Use for | Covers |
|---|---|---|
| `frontend-development` | UI, components, styling, client state, a11y | Angular, React, Next.js, Vue, accessibility, CSS, component testing, client performance |
| `backend-development` | APIs, services, data access, auth | NestJS, Node.js, Java, Spring Boot, Python, API design, databases (SQL, MongoDB, Elasticsearch, Redis), auth/security, integration testing |
| `core-development` | The baseline shared by both | TypeScript, JavaScript, clean code, architecture, NX, Docker, GitHub Actions, documentation, testing, git/gitflow, security, versioning |

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

## issue-delivery

One skill, `deliver-issue`. It takes an issue from the tracker to an open pull request, following the project's own standards. It owns the issue lifecycle and delegates the rest.

- **Flow:** fetch and check eligibility, assign and branch, analyse and plan (with your go), implement, test, open the PR, offer a self-review, and update the board.
- **Trackers:** GitHub, GitLab, and Jira. On Jira the issue lifecycle stays in Jira while the code and PR live on the linked git host.
- **Harmonises with the others:** git and coding standards and dependency vetting come from `clean-code`, and the optional self-review runs `code-review`.

It never merges, and it never codes without an approved plan.

```
/plugin install issue-delivery@ai-skills
```

The per-plugin `/plugin install` examples above are Claude Code commands. In Codex, use `codex plugin add <plugin>@ai-skills`.

## Layout

```
.claude-plugin/marketplace.json      Claude Code catalog
.agents/plugins/marketplace.json     Codex catalog
clean-code/
  .claude-plugin/plugin.json         Claude Code manifest
  .codex-plugin/plugin.json          Codex manifest
  skills/
    frontend-development/  SKILL.md + references/
    backend-development/   SKILL.md + references/
    core-development/       SKILL.md + references/
code-review/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/
    review-changes/        SKILL.md + references/
epic-planning/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/
    plan-epic/             SKILL.md + references/ (+ platforms/)
devops/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/
    deployment/            SKILL.md + references/
issue-delivery/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/
    deliver-issue/         SKILL.md + references/ (+ platforms/)
```

## Manual install

The skills are plain Markdown. To install all seven in Codex without marketplace support, run this from a persistent checkout of the repository:

```bash
mkdir -p ~/.agents/skills
for skill in "$PWD"/*/skills/*; do
  ln -s "$skill" ~/.agents/skills/
done
```

For Claude Code, use `~/.claude/skills/` instead. The links depend on this checkout remaining at the same location. `ln` refuses to overwrite existing entries; inspect a conflict before replacing anything. Use either marketplace installation or manual links for a given skill to avoid duplicate discovery. Start a new conversation after installing.

## Extending

**Add a stack to a skill:** drop a new `references/<stack>.md` into the right skill and add a row to the detection table in its `SKILL.md`.

**Add a new plugin:** create a sibling folder with `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and one shared `skills/` directory. Register it in both marketplace catalogs with the same name and source directory.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide and the house style.

## License

[MIT](LICENSE).
