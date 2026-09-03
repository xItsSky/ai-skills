---
name: deliver-issue
description: Use when taking an issue from a tracker to an open pull request. Triggers on "take issue #X", "implement issue #X", "pick up issue #X", "work on issue #X", "deliver #X". Works with GitHub, GitLab, and Jira. Fetches the issue, branches, analyses, implements to the project's standards, tests, opens the pull request, and updates the board. Never merges.
---

# Deliver Issue

Take an issue from the tracker to an open pull request, following the project's own standards. This skill owns the issue lifecycle and the tracker plumbing. It delegates coding standards, git conventions, dependency vetting, testing, and review to the other skills. It never merges.

## Delegation

Do not restate what these cover; use them:

- Branch naming, commits, and gitflow: the `clean-code` skill (`git-gitflow`).
- Coding standards for the detected stack, and dependency vetting: the `clean-code` skill.
- The testing contract: the `clean-code` skill (`testing-philosophy`).
- Self-review of the diff: the `code-review` skill (`review-changes`).

## Step 1: Identify the issue and tracker

- Get the issue reference from the user or a parameter.
- Determine the tracker: a parameter wins; otherwise detect it (git remote host, an available CLI such as `gh`, `glab`, or `jira`, a config file); otherwise ask.
- Read only `references/platforms/<tracker>.md`.

## Step 2: Fetch and check eligibility

Fetch the issue: title, description, linked context, status, assignee, iteration or sprint. Confirm it is a sound pick: open, not already assigned to someone else, and in a ready state (To Do or the project's equivalent). If a check fails, stop and tell the user instead of proceeding.

## Step 3: Assign and start

Assign the issue to the current user and move it to In Progress. Create the working branch off the base branch, using the convention from `clean-code` (`git-gitflow`), tied to the issue number.

## Step 4: Analyse before coding

Work through `references/analysis.md`: understand the issue against the codebase, find the affected areas, and produce a short plan. Present the plan and wait for the user's go before writing code.

## Step 5: Implement

Implement the change following the `clean-code` standards for the detected stack. Vet any new dependency before installing it. Keep the change scoped to the issue.

## Step 6: Test and validate

Add tests to the `clean-code` testing contract. Run the project's build and test commands. Do not proceed while they are red.

## Step 7: Commit, push, open the PR

Commit with Conventional Commits, push the branch, and open the pull or merge request using the repository template. Link the issue so the tracker cross-references it.

## Step 8: Offer a self-review

Offer to run the `code-review` skill on the diff before handing back. Report or post the findings, and fix what is worth fixing.

## Step 9: Update the tracker

Move the issue to the review state and update the board. Keep status transitions honest with the actual state of the work.

## Step 10: Summary

Report the issue, the branch, the pull request link, the test status, and the tracker state.

## Rules

- Never merge, approve, or formally request changes. The decision belongs to the reviewer.
- Never code without an approved plan.
- Never skip tests or push past a red build.
- Never invent tracker metadata. Resolve statuses, labels, and fields from the tracker.
- One issue per run.
