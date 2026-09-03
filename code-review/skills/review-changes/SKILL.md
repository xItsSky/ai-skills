---
name: review-changes
description: Use when performing a first-pass code review of a change set before a human reviewer. Triggers on "review my changes", "review this diff", "do a code review", "first pass on PR #X", "review MR !X". Reviews a local working-tree diff, a branch against its base, or a GitHub or GitLab pull or merge request. Never approves, merges, or formally requests changes.
---

# Review Changes

A thorough first-pass review of a change set. Get the diff from wherever it lives, review it across several dimensions in parallel, and report findings as Conventional Comments. This is a first pass for a human reviewer, never a gate. It does not approve, merge, or formally request changes.

## Step 1: Get the diff

Identify the review target and collect the diff, the list of changed files, and enough surrounding context to review each change in place. The target is one of:

- the local working tree (uncommitted or staged changes),
- a branch compared to its base,
- a GitHub pull request or GitLab merge request.

See `references/diff-sources.md` for the exact commands per source and how to tell which one applies.

## Step 2: Understand the intent

Read what the change is trying to do before reviewing it: the pull or merge request title and description, the linked issue, and the commit messages. Review against the intent, not only the lines.

## Step 3: Detect the stack and load conventions

Detect the languages and frameworks in the changed files (`package.json`, `pom.xml`, `build.gradle`, file extensions). Then load the standard to review against:

- If the `clean-code` plugin from this marketplace is available, use its stack references (for example `react.md`, `spring-boot.md`, `testing-philosophy.md`) as the baseline.
- Otherwise apply general best practice and honour the project's own conventions: CONTRIBUTING, CLAUDE.md or AGENTS.md, linter and formatter configs.

Run the dependency vulnerability audit and pass its results to the security pass. The commands and thresholds are in `references/review-dimensions.md`.

## Step 4: Review in parallel

Launch one subagent per review dimension, in parallel. Give each the diff, the intent from Step 2, the loaded conventions, and its brief. Scale the set to the change: a one-file fix does not need every dimension.

The dimensions and their checklists are in `references/review-dimensions.md`: Correctness, Security, Architecture, Tests, Performance, Readability, Documentation, and an optional Runtime pass.

## Step 5: Consolidate

Collect every finding and prepare the final set:

- Deduplicate. If two passes flag the same line for the same reason, keep the most useful comment.
- Mark blocking or non-blocking on purpose. Default to non-blocking when unsure.
- Include at least one genuine `praise`. Do not fabricate it.
- Verify every comment follows the format in `references/conventional-comments.md`.

## Step 6: Deliver

- If the target is a pull or merge request and the platform CLI is available and authenticated, post the findings as inline review comments. See `references/posting-adapters.md`.
- Otherwise, output a local report: findings grouped by file and line, each written as a Conventional Comment.

## Step 7: Summary

Close with a short summary: the target reviewed, the number of findings, the blocking, non-blocking, and praise counts, and the top three concerns in one line each. No emoji.

## Rules

- Never approve, merge, or formally request changes. This is a first pass. The decision belongs to the author and the human reviewer.
- On a platform, post as comments only. Never send an approve or request-changes event.
- Every comment uses the Conventional Comments format. No free-form remarks.
- Blocking is for clear bugs, security holes, or broken functionality. Everything else is non-blocking.
- Be constructive. Suggest and explain. The author knows the codebase too.
