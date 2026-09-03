---
name: plan-epic
description: Use when turning a feature idea into a complete epic and its stories on an issue tracker. Triggers on "create an epic", "plan a feature", "let's spec out X", "I want to build X", "break X into stories". Works with GitHub, Jira, and Trello. Runs a challenge-driven discovery, drafts the epic and stories with their relations and metadata, then creates them only after explicit approval. Never creates anything without approval.
---

# Plan Epic

Turn a feature idea into a complete epic and its stories on the project's tracker. The conversation comes first and it is demanding: the goal is a specification with no soft spots, centred on business rules. Technical detail lives in the stories, not the epic. Nothing is created until the full plan is approved.

## Step 1: Discover and challenge

Have a real conversation. Ask progressively, two or three questions at a time, and rephrase what you understood before going deeper. Do not dump a form.

Challenge the idea until it is complete. Hunt for the gaps: unstated business rules, edge cases, error and empty states, permissions, data lifecycle, and non-functional needs. When the user is vague, propose a concrete interpretation and ask them to confirm or correct it. Work through `references/challenge-checklist.md`.

Leave this step only when you can write solid epic acceptance criteria and enumerate the business rules with confidence. Park anything still open as an explicit assumption or question. Do not paper over it.

## Step 2: Determine the tracker

Find where the work will live, in this order:

1. If the user named a tracker or passed one as a parameter, use it.
2. Otherwise detect it: the git remote host, an available CLI (`gh`, `jira`, a Trello token), a connected MCP server, or a config file.
3. Otherwise ask.

Read only `references/platforms/<tracker>.md` for the one that applies.

## Step 3: Draft the epic

Write the epic to the structure and quality bar in `references/epic-spec.md`: context, the full functional description, an explicit business-rules section, scope and non-goals, epic-level acceptance criteria, and dependencies. Keep technical design out; it belongs in the stories.

Present the draft and ask what to adjust. Do not move on until the user approves it.

## Step 4: Draft the stories and relations

Decompose the epic into work items using `references/story-breakdown.md` (types, story format, estimation) and `references/relations.md` (parent/child, needs, depends-on, blocks, relates-to). Each story carries its user-story statement, the business rules it enforces, acceptance criteria, and technical notes. Show the list and the relation graph.

If the `clean-code` plugin is installed, use its stack references for the technical notes.

Present and refine until the user approves the set.

## Step 5: Groom

Offer to groom the stories, the user's choice:

- With the user: refine acceptance criteria, split oversized stories, add missing edge-case stories, and estimate together.
- On your own: groom to a consistent bar, then present the result for review.

Grooming detail is in `references/story-breakdown.md`.

## Step 6: Sprint placement

Only if the tracker uses sprints or iterations. Offer to place stories into one: current, next, or a named sprint. Never assume, and never put the epic in a sprint. Skip this step entirely when there are no sprints.

## Step 7: Preview the full plan

Before creating anything, show a dry run of exactly what will be created: every item with its type, the relations between them, the resolved metadata, and any sprint placement. Get explicit approval on the whole plan.

## Step 8: Create

Create the items through the platform adapter: the epic, the stories and sub-tasks, their types and metadata, the relations, and any sprint placement. Resolve metadata against the tracker's real options (list them first). Never invent a label, field, or value. If a value is unclear, ask.

## Step 9: Summary

Report what was created: the epic and its link, each story with its type and estimate, the relations set, and any sprint. Keep it plain, no emoji.

## Rules

- Nothing is created without explicit approval of the full plan. Every draft gate is mandatory.
- The user has the final say on every choice. When unsure, ask.
- The epic centres on business rules and outcomes. Technical detail goes in the stories.
- Never invent metadata. Resolve types, labels, fields, milestones, and sprints from the tracker.
- Epics never go in a sprint.
- One epic per run. Do not chain several without separate approval for each.
