# Security Baseline

Cross-cutting rules that apply to any code in any stack. They are cheap to follow while writing and expensive to retrofit after a breach. Treat them as defaults, not as a hardening phase you do later.

## Trust nothing from outside

- Validate every input at the boundary it enters: request bodies, query params, headers, file uploads, message payloads, env values. Reject what does not match the expected shape.
- Validate against an allowlist of what is permitted, not a blocklist of what is banned. Blocklists always miss a case.
- Sanitize before use, and validate before you sanitize. A well-formed value is easier to reason about.

## The client is hostile

- Anything running in the browser or on a device can be read, modified, and replayed. Never rely on client-side checks for security.
- Enforce authorization and validation on the server for every request, even ones a legitimate client would never send.
- Do not ship secrets, private keys, or internal endpoints in client bundles. They are public the moment they build.

## Secrets

- Keep secrets out of the repository. No API keys, tokens, or passwords in source, config committed to git, or history.
- Load them from environment variables or a secret manager, injected at deploy time.
- Rotate secrets on a schedule and immediately if one leaks. Assume anything committed once is compromised forever.

## Least privilege

- Grant the minimum access needed and nothing more: database roles, API scopes, file permissions, cloud IAM, service accounts.
- Scope credentials narrowly and separate them per environment. A read path does not get write access.

## Injection

- Use parameterized queries or a query builder for every database call. Never build SQL by concatenating input.
- The same rule holds for shell commands, LDAP, and NoSQL filters: pass data as data, never splice it into the command string.
- When interpolation is unavoidable, use the platform's escaping API for that exact target.

## Output encoding

- Encode output for the sink that consumes it: HTML-escape for markup, attribute-escape for attributes, JSON-encode for scripts, URL-encode for URLs.
- The right encoding depends on where the value lands, so choose it at the point of output, not at input.

## Dependencies

- Keep dependencies patched. Run an audit in CI and update on known vulnerabilities.
- Keep the dependency tree minimal. Every package is code you now trust and attack surface you now own.
- Pin versions and review what a new or updated dependency pulls in.

## Before adding a dependency

Adding a package is a security decision, not a convenience. Vet every new or upgraded dependency before it enters the manifest, in any ecosystem (`npm install`, Yarn, pnpm, Maven, Gradle, `pip`, `go get`, Cargo).

- Vet first, install second. Do not run the install command until the package has cleared this check.
- Audit the exact version you intend to add, and its transitive tree, against a known-vulnerability source: `npm audit` / `pnpm audit` / `yarn npm audit`, OWASP Dependency-Check for Maven or Gradle, `pip-audit`, `govulncheck`. Cross-check the advisory databases (GitHub Advisories, OSV, Snyk).
- Also weigh basic supply-chain health: is it maintained, widely used, and free of active advisories? An unmaintained or typosquatted package is a risk even with no CVE.
- If the package or anything it pulls in has known vulnerabilities, stop. Do not install it. Report the findings to the user: the package, the affected version, the severity, and a link to the advisory. Wait for the user's explicit decision before proceeding.
- Proceed only when the tree is clean, or when the user has knowingly accepted the risk. Prefer a patched version or a safer alternative when one exists.

## Fail closed

- On error, ambiguity, or timeout, deny. A failed auth check must reject, never fall through to allowed.
- Default to the safe state. If you cannot confirm access, refuse it.

## Logging

- Do not log secrets, tokens, passwords, or PII. Logs travel to places with weaker controls than your database.
- Redact sensitive fields before they reach a log line, and be deliberate about what error detail you expose to a client.

## Cryptography

- Use vetted, maintained crypto libraries. Never invent your own cipher, hash scheme, or token format.
- Hash passwords with a slow algorithm built for it (argon2, bcrypt, scrypt), never a plain SHA.
- Let the library handle salts, IVs, and modes; misusing a primitive breaks it as surely as a weak one.

## Transport

- Enforce HTTPS everywhere and redirect plaintext to it. Enable HSTS.
- Use TLS for service-to-service traffic too, and verify certificates. Internal does not mean trusted.

## Do / Instead of

| Do | Instead of |
|---|---|
| Validate against an allowlist at the boundary | trust well-formatted input |
| Enforce authz on the server | rely on hidden UI or client checks |
| Load secrets from a secret manager | commit keys to the repo |
| Grant least privilege per role | share one broad admin credential |
| Parameterized queries | string-concatenated SQL |
| Encode output for its sink | insert raw values into HTML/URLs |
| Audit and patch dependencies | pin once and forget |
| Vet and audit a dependency before installing | `npm install` first, check later |
| Surface vulnerabilities and wait for approval | add a flagged package silently |
| Deny on error (fail closed) | fall through to allowed |
| Redact secrets and PII from logs | log full request or user objects |
| Vetted crypto libraries | hand-rolled encryption |
| HTTPS/TLS with cert verification | plaintext on "internal" networks |
