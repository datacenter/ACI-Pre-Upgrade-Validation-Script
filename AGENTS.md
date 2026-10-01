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
