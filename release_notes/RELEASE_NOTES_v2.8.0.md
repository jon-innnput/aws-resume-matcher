# Release Notes: v2.8.0

v2.8.0 adds deterministic requirement intelligence and confidence scoring to semantic-mode explainable fit analysis.

This release keeps keyword-only behavior unchanged. It does not change infrastructure, workflows, SAM runtime configuration, AWS resources, embedding cache design, top-level score semantics, or the request contract.

## Highlights

- Added conservative requirement classification for semantic-mode fit analysis:
  - `required`
  - `preferred`
  - `responsibility`
  - `experience`
  - `credential`
  - `other`
- Added deterministic requirement priority bands:
  - `high`
  - `medium`
  - `low`
- Added semantic-mode match confidence bands:
  - `high`
  - `medium`
  - `low`
- Added concise deterministic rationales explaining priority and match confidence.
- Added a compact semantic-mode `fit_summary` with requirement counts, high-confidence matches, and high-priority gaps.
- Calibrated requirement filtering and confidence thresholds against real resume/job-description samples before release.
- Reduced non-requirement boilerplate from verbose job postings, including application windows, benefits, compensation ranges, company/team narrative, and title-like headers.
- Split oversized recruiting narrative into a capped set of atomic requirement concepts when clear actionable signals are present.
- Dropped narrative-only blocks from requirement scoring when no meaningful atomic requirement can be extracted.
- Preserved keyword-only response shape and behavior.

## Why This Release

v2.5.0 introduced explainable fit analysis with matched requirements, gaps, and supporting resume evidence. v2.5.1 calibrated the match threshold against real Bedrock/Titan behavior. v2.6.0 and v2.7.0 improved evidence retrieval and selection.

v2.8.0 builds on that foundation by making the fit analysis more useful to reviewers. Instead of returning only a requirement score, the API now labels what kind of requirement was parsed, how important it appears to be, and how confident the matcher is in the selected evidence.

The implementation is intentionally deterministic. It uses conservative heuristics, existing scoring signals, keyword overlap, semantic score, alias overlap, and evidence quality. It does not use LLM extraction, learned weighting, or new dependencies.

Before release, the heuristics were calibrated against the repository's real sample resume and job-description files. That calibration tightened requirement extraction so job-posting metadata, benefits text, compensation ranges, application-window notices, company narrative, and title-like headers are less likely to appear as gaps. It also prevents large recruiting-marketing paragraphs from being scored directly as requirements. When those paragraphs contain recognizable actionable concepts, they are converted into a small number of atomic requirements such as program management, data fluency, business analysis, content strategy, stakeholder communication, automation, AI/ML tools, cloud platform experience, data pipelines, and self-service tooling. It also improved confidence calibration so strong direct keyword or alias evidence can produce `high` confidence, while semantic-only midrange matches remain conservative.

## Semantic-Mode Response Additions

Each `matched_requirements` item now includes:

- `requirement_type`
- `priority`
- `confidence`
- `rationale`

Each `gaps` item now includes:

- `requirement_type`
- `priority`
- `confidence`
- `rationale`

Semantic-mode responses also include:

```json
{
  "fit_summary": {
    "total_requirements": 2,
    "matched_count": 1,
    "gap_count": 1,
    "high_confidence_matches": 1,
    "high_priority_gaps": 1
  }
}
```

Keyword-only responses are unchanged and still return only:

- `score`
- `matching_keywords`
- `missing_keywords`

## Preserved Behavior

- Lambda runtime remains Python 3.12.
- GitHub Actions runners remain Python 3.13.
- Semantic matching remains guarded behind `SEMANTIC_MATCHING_ENABLED`.
- Keyword-only mode remains the default production behavior.
- Top-level semantic scores keep their existing meanings.
- No SAM resources, IAM policies, deployment workflows, or AWS resources changed.
- No new dependencies were added.
- The v2.7.1 documentation-only release note remains separate from this feature release.

## Calibration Caveats

The new `requirement_type`, `priority`, `confidence`, and `rationale` fields are deterministic reviewer aids, not statistically learned predictions.

Confidence is intentionally conservative. A requirement can meet the calibrated match threshold and still receive `low` confidence when support is mostly semantic, weakly overlapping, or narrow. Strong direct keyword overlap, phrase-alias support such as `AI/ML` to `artificial intelligence` / `machine learning`, or clear program-management evidence can raise confidence when the selected evidence is strong enough. Priority is based on heuristic signals such as must-have language, years of experience, credentials, security/compliance terms, cloud/platform/tool terms, and explicit technical skills.

## Validation

- Added focused unit tests for requirement classification and priority heuristics.
- Updated semantic-mode response-shape tests for requirement intelligence fields and `fit_summary`.
- Added regression tests for sample-style job posting boilerplate and Unicode resume bullets.
- Added regression tests for splitting recruiting narrative into atomic requirements.
- Updated confidence calibration tests for direct phrase-alias matches.
- Confirmed keyword-only response shape remains unchanged.
- Confirmed SAM template validation and SAM build remain available without infrastructure changes.
