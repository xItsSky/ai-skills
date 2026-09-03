# Versioning and Migration

Framework conventions change between major versions. A rule that is correct on the latest version can be wrong on an older one. Detect the version before applying version-specific guidance, and never change a project's versions without the user's approval.

## Detect the version first

- Read the installed version from the source of truth: the lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`) over the range in `package.json`; the resolved version from `pom.xml`, `build.gradle`, or the dependency tree on the JVM.
- Use the resolved version, not the declared range. `^17.0.0` may resolve to 17.3, or the lockfile may pin something else.
- Note the major, and the minor when a rule depends on it.

## Apply the guidance that matches the version

- Reference files label version-specific rules, for example "default from v20". Apply the rule that matches the detected version, not the newest one.
- On an older version, do the older thing. Angular standalone components are the default from v20, so on v17 you still set them explicitly. Do not apply a v22 rule to a v17 project.
- The generic, version-independent rules always apply.

## Check support and available upgrades

- Check whether the detected version is still supported or has reached end of life. Release and LTS schedules move, so confirm against current information rather than memory.
- Check whether a newer stable major exists.
- If the version is end of life, unsupported, or well behind the current stable, tell the user. State the risk, name the current stable, and outline the migration path.

## The user decides

- Surface the finding with a recommendation. Do not upgrade dependencies, bump a major, or run a migration on your own.
- Wait for explicit approval before changing any version. The final call is the user's.

## Do / Instead of

| Do | Instead of |
|---|---|
| Read the resolved version from the lockfile | assume the latest major |
| Apply rules matching the detected version | apply the newest convention everywhere |
| Flag EOL or unsupported versions with a migration path | silently keep building on an EOL version |
| Propose a major upgrade and wait for approval | bump majors on your own |
