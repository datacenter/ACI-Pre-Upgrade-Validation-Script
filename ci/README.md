# Publishing actual-version integration results

Run the full actual-version validation and publish its snapshot:

```bash
git push gitlab HEAD -o ci.variable="PUBLISH_ACTUAL_RESULTS=true"
```

The opt-in flag adds `publish:actual-version-results` in a third
`publish_results` stage. Unit tests still run, and the six version-override
integration jobs are omitted for this flagged run. Without the flag, all seven
integration jobs retain their normal behavior. The publisher downloads artifacts only from
`test:integration:actual-current-version`, including when that job fails.
Do not combine publication with `INTEGRATION_CHECK`; focused results are rejected.

The runner must support `--results-dir`. Deploy the companion runner change to
its GitLab `main` branch first. For development, `INTEGRATION_RUNNER_REF` can
select a runner branch through another `ci.variable` push option. Requirements
and the fabric inventory continue to come from `main`.

Store `RESULTS_GITHUB_TOKEN` in the source GitLab project's Settings → CI/CD →
Variables. Use a dedicated credential able to push to the results repository,
mask it, hide it when supported, and disable variable expansion. If protected,
the publishing pipeline must run on a protected branch or tag. The credential
is used by an ephemeral Git askpass helper; it is never embedded in the Git URL.

Set `RESULTS_GITHUB_REPOSITORY` to the destination HTTPS repository URL without
credentials. It may be a GitLab variable or a second `ci.variable` push option.
Results are committed to `master` by default; `RESULTS_GITHUB_BRANCH` can select
another existing branch. The destination may be GitHub or GitHub Enterprise.
Each fabric folder contains the actual validator report as `results.log`, the
unchanged bundle as `results.tgz`, and `error.txt` for execution or collection
failures. Lossy-group connection warnings are included even when the integration
job succeeds. Validator check FAILs and check errors remain in the report.
No console transcript is substituted for a missing validator report.

The root README shows totals for integration failures, validator check errors
(`ERROR !!`), and validator check FAILs (`FAIL`), plus separate per-fabric columns.
It highlights fabrics with check errors and links to the affected checks. Each
fabric's README shows its source pipeline, commit, run date, and result details.
`error.txt` is reserved for integration execution or collection failures and
includes this provenance even when a repeated failure has identical diagnostics.
An unavailable or unrecognized validator summary is shown explicitly and is
excluded from validator totals; it is never treated as zero errors or a pass.

`manifest.json` records source provenance, per-fabric completion, integration
diagnostics, and separate validator error/finding counts and check links. Later publications remove the preceding
snapshot's fabric folders and stale errors while preserving repository metadata.
Publications are serialized; older pipeline results cannot replace newer results
from the same source project. Missing or invalid artifacts and GitHub push
failures fail the publisher without changing the remote snapshot.

GitLab does not guarantee artifact upload after a whole-job timeout or
cancellation. If no manifest is available, publication fails and the previous
snapshot remains. Individual fabric SSH timeouts are recorded in the snapshot.

After review, create a GitHub release with a new tag at the exact results commit.
Release creation is manual. Replacing current files uses normal commits, so prior
tags and Git history remain available; old bundle data is not removed from history.

Run publisher regression tests with:

```bash
python3 -m unittest discover -s ci/tests -p 'test_*.py'
```

The local Git fixture is skipped when Git is unavailable, including in the slim
Python unit-test images. The publishing job installs Git and runs this complete
regression suite before publishing, so the Git fixture is exercised there.

The validator and this workflow are sourced from GitHub. Push the requested
GitHub commit to GitLab for execution; no release-specific scripts need to be
injected into the source branch. Fabric inventories, connection credentials,
and the destination repository are supplied privately through GitLab variables.
