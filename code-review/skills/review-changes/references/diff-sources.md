# Diff Sources

Detect the target, then collect the diff, the changed-file list, and surrounding context. Read enough of each changed file to review it in context, not just the hunks.

## Which source

- A pull or merge request number, a URL, or an explicit ask ("review PR #12") means the platform source. Choose GitHub or GitLab by the remote or the available CLI.
- "Review my changes" with uncommitted work means the working tree.
- "Review this branch", or a named base, means branch against base.

When it is unclear, ask. Failing that, default to the working tree if there are uncommitted changes, otherwise the current branch against the default branch.

## Working tree

```bash
git status --short          # scope of the change
git diff                    # unstaged
git diff --staged           # staged
git diff HEAD               # both, against the last commit
```

## Branch against base

```bash
# default branch of the remote, unless the user names a base
base=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
git diff "$base"...HEAD              # changes introduced on this branch
git diff --name-only "$base"...HEAD  # changed files
```

## GitHub pull request

```bash
gh pr view <n> --json number,title,body,baseRefName,headRefName,author,files
gh pr diff <n>
gh pr diff <n> --name-only
```

## GitLab merge request

```bash
glab mr view <n>
glab mr diff <n>
```

Read the title, description, and linked issue for intent before reviewing (Step 2 of the skill).
