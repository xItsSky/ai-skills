# Conventional Comments

Every finding is written in this format, whether it lands in a local report or a platform comment.

```
**<label> [(<decoration>)]:** <subject>

[optional discussion]
```

Keep the subject short. Put the reasoning and any suggested fix in the discussion.

## Labels

| Label | When to use |
|---|---|
| `praise` | Something genuinely well done. Leave at least one per review. |
| `suggestion` | A proposed improvement, with a clear what and why. |
| `issue` | A concrete problem. Pair it with a suggestion when you can. |
| `question` | Uncertainty. You are not sure it is a problem and want clarification. |
| `nitpick` | Trivial style preference. Always non-blocking. |
| `todo` | A small necessary change before merge. |
| `thought` | An idea or alternative worth considering. Always non-blocking. |
| `chore` | A process task before merge, such as updating docs or running a job. |
| `note` | Informational. Always non-blocking. |
| `typo` | A misspelling, like `todo` but for text. |
| `polish` | Not wrong, but could be cleaner. |

## Decorations

| Decoration | Meaning |
|---|---|
| `(blocking)` | Must be resolved before merge. |
| `(non-blocking)` | Can merge as is, address later. |
| `(if-minor)` | Resolve only if the fix turns out trivial. |
| `(security)` | Security concern. |
| `(performance)` | Performance concern. |
| `(test)` | Test coverage or quality concern. |
| `(runtime)` | Found or confirmed by running the code. |

## Examples

```
**issue (blocking):** The access token is logged in plain text here.

This exposes credentials in the logs. Redact it, or drop the log line entirely.
```

```
**suggestion (non-blocking):** Extract this into a reusable `formatDate` helper.

It appears in three places already. Centralising it makes the next change cheaper.
```

```
**praise:** Clean separation between the service and the handler. The boundary is exactly right.
```

```
**nitpick (non-blocking):** `getUsersList` reads better as `getUsers`.

The plural already implies a collection, so the `List` suffix is redundant.
```
