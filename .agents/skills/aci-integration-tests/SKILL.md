---
name: aci-integration-tests
description: Run, monitor, and interpret this repository's GitLab integration pipelines, including focused runs of one validation function through the INTEGRATION_CHECK push variable. Use when testing a branch against live ACI fabrics or reviewing those pipeline results. Do not use for local pytest-only work.
---

# ACI Integration Tests

Use the `gitlab` remote for live-fabric integration tests. Preserve unrelated
working-tree changes and never print values from `.env`.

## Choose the Run

Use a focused run while developing or validating one check. Use the exact
Python function registered in one of the `CheckManager` check lists in
`aci-preupgrade-validation-script.py`; do not infer it from a test directory or
documentation title. Some registered functions do not end in `_check`.

Confirm the function before pushing:

```bash
rg -n "def <function_name>|^[[:space:]]+<function_name>," aci-preupgrade-validation-script.py
```

Push the current commit and attach the selector only to the pipeline created by
that push:

```bash
git push -u \
  -o ci.variable="INTEGRATION_CHECK=<function_name>" \
  gitlab HEAD:<branch_name>
```

Repeat `-o ci.variable=...` on every later push that should remain focused.
GitLab push variables do not become persistent branch configuration. A retry of
the same pipeline retains its original variables.

For a complete validation run, omit the push variable:

```bash
git push -u gitlab HEAD:<branch_name>
```

Never encode the selected check in the branch name. `INTEGRATION_CHECK` is the
workflow's explicit selector.

## Expected Pipeline Behavior

- Python 2.7 and Python 3.8 unit-test jobs still run normally.
- All configured integration version jobs are created. In focused mode, each
  job runs the selected function across the fabric inventory.
- The integration jobs share `resource_group: aci_fabric_tests`, so GitLab runs
  them serially and reports the others as `waiting_for_resource`.
- The runner logs `Running only integration check <function_name>` before
  connecting. Confirm this line before interpreting the result as focused.
- Fabrics in the inventory's `lossy` group may report socket timeouts or SSH
  authentication failures as warnings. Validation errors after a successful
  connection remain fatal.
- An unknown or unavailable function must fail before fabric connections. Do
  not accept a zero-check pipeline as success.

## Monitor and Report

Use `GITLAB_URL` and `GITLAB_TOKEN` from `.env` for read-only GitLab API calls.
Keep the token in request headers and out of commands or output that could expose
it. Resolve the project, then inspect the newest pipeline for the exact pushed
branch, its jobs, and relevant job traces. Do not assume the globally newest
pipeline belongs to the requested branch.

Report:

- Pipeline ID, branch, commit SHA, status, and GitLab link.
- Whether the run was focused and the exact function selected.
- Unit-job status and every integration scenario's status.
- Required fabric connection failures, optional connection warnings, and real
  validation errors as separate categories.
- Any jobs still running or waiting for the shared resource.

Treat a pipeline as complete only when all non-skipped jobs reach a terminal
state. Do not cancel, retry, merge, or delete a branch unless the user requests
that external change.
