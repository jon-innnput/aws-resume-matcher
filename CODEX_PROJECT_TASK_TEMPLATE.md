# Codex Project Task Template

Use this template for all non-trivial coding tasks.

---

## Context

Inspect the entire repository before making changes.

Review:

* README.md
* CONTEXT.md
* Existing architecture
* Existing workflows
* Existing deployment process
* Current version history

Do not assume features exist unless they are present in the repository.

---

## Objective

[Describe the feature, enhancement, bug fix, refactor, infrastructure change, documentation update, or research task.]

---

## Constraints

* Preserve existing functionality unless explicitly instructed otherwise.
* Prefer incremental, reviewable changes.
* Minimize scope creep.
* Follow existing project conventions.
* Do not introduce unnecessary dependencies.
* Explain tradeoffs when multiple approaches exist.

---

## Documentation Requirements

Determine whether the following should be updated:

* README.md
* CONTEXT.md

For each file:

* Explain whether an update is needed.
* Update only if justified by the change.

If version history exists, update it when appropriate.

---

## Implementation Process

Before making changes:

1. Explain the proposed approach.
2. Identify risks and assumptions.
3. Identify files likely to change.

After making changes:

1. List all files changed.
2. Explain why each file changed.
3. Summarize implementation details.
4. Explain any design decisions.

---

## Testing Requirements

Determine appropriate validation.

Possible examples:

* Unit tests
* Integration tests
* Build validation
* Linting
* SAM validation
* Docker validation
* API testing

Run or describe all validation performed.

---

## Release Management

Assess the impact using Semantic Versioning (SemVer).

Recommend one:

* Patch release (x.y.Z)
* Minor release (x.Y.z)
* Major release (X.y.z)

Provide:

### Recommended Version

Example:

v1.3.0

### Recommended Tag

Example:

v1.3.0

### Release Classification

* Patch
* Minor
* Major

### Release Summary

Provide a concise release summary suitable for GitHub Releases.

---

## Git Workflow

Provide:

### Suggested Branch Name

Example:

feature/pytest-test-suite

### Suggested Commit Message

Example:

Add pytest-based automated test suite

### Suggested PR Title

Example:

Add automated testing with pytest

### Suggested PR Description

Include:

* Summary
* Changes
* Validation
* Risks
* Documentation updates

---

## Deliverables

Return:

1. Proposed approach
2. Files changed
3. Implementation summary
4. Validation performed
5. Documentation updates
6. Version recommendation
7. Branch name
8. Commit message
9. PR title
10. PR description
11. Draft release notes

---

## Future Roadmap Impact

Assess whether this change affects:

* Current roadmap
* Technical debt
* Future releases
* Architecture decisions

If yes, update CONTEXT.md accordingly.

---

## AWS-Specific Requirements

* Prefer Infrastructure as Code.
* Prefer GitHub OIDC over long-lived credentials.
* Consider CloudFormation/SAM implications.
* Consider CI/CD implications.
* Consider AWS cost impact.
* Prefer free-tier or near-zero-cost approaches when reasonable.
