# Agent Instructions

Before running, monitoring, or interpreting live ACI integration tests, load
and follow `ACI-PUV-Developers/aci-integration-tests` from the CX Skills
platform with the `cx-skills` CLI.

Install it into a fresh temporary directory outside this repository:

```sh
cx-skills install ACI-PUV-Developers/aci-integration-tests --dir <temporary-directory> --json
```

Read the installed `SKILL.md` before acting. Refresh it at the start of each
integration-test task, and never commit the downloaded skill files here.

## Test scope

Automated tests must cover only data, logic, and `RESULT` values. Do not add or
update tests for user-facing wording, messages, recommended actions,
documentation prose, punctuation, capitalization, or other presentation text.
For wording-only changes, run the existing relevant tests without creating or
modifying test coverage for the wording.

## Manual result messaging

For a `MANUAL` result, populate `msg` only as a short heads-up when neither
`data` nor `recommended_action` is provided. When a result includes data or
needs explanation or remediation guidance, leave `msg` empty and put the full
explanation and action in `recommended_action`.

## Documentation links

Never put link destinations directly in documentation prose. Use the
document's existing numbered reference-link system, adding the next appropriate
reference definition when a new destination is needed.
