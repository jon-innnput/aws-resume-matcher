# Release Notes: v2.7.1

v2.7.1 is a documentation reconciliation release for AWS Resume Matcher.

This release does not change application code, infrastructure code, CI/CD behavior, Lambda runtime configuration, scoring logic, semantic matching behavior, or the public API contract.

## Highlights

- Reconciled repository documentation around the current runtime model.
- Confirmed the CloudFormation-managed Lambda runtime remains Python 3.12.
- Confirmed GitHub Actions CI/CD runners use Python 3.13 for tests, SAM validation/build orchestration, and source compilation.
- Documented that no Python runtime migration is planned.
- Clarified that the active production Lambda is the SAM/CloudFormation-managed `ResumeMatcherFunction`.
- Documented that a likely orphaned standalone Lambda named `resume-matcher` was identified but not acted upon.
- Preserved the v2.7.0 feature scope and behavior.

## Why This Release

The runtime investigation found that the project has an intentional split between the deployed Lambda runtime and the GitHub Actions runner runtime. The deployed Lambda remains on Python 3.12, while CI/CD uses Python 3.13 on the runner.

v2.7.1 records that conclusion so future work does not reopen the runtime migration question unnecessarily or confuse the active CloudFormation-managed Lambda with unrelated standalone Lambda resources.

## Preserved Behavior

- Lambda runtime remains Python 3.12.
- GitHub Actions runners remain Python 3.13.
- Keyword-only behavior remains the default production behavior.
- Semantic matching remains guarded by `SEMANTIC_MATCHING_ENABLED=false` in the SAM template.
- No request or response fields changed.
- No SAM resources, IAM policies, or deployment workflow logic changed.
- No scoring, evidence retrieval, or explainable-fit logic changed.

## Validation

The v2.7.1 release completed successfully with:

- CI/CD validation.
- SAM deployment.
- Automated tests.
- Local validation.
- Production deployment.

## Follow-Up Notes

Future feature release notes should remain separate from this documentation-only release. The next roadmap milestone should use its own version-specific release note file.
