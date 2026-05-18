---
name: eval-review
description: audit forecast agent responses for required tools, selected skills, citations, probabilities, and unsupported certainty claims.
---

# Skill: eval-review

## Purpose
Audit agent responses for the episode evaluation harness.

## Use when
- Running evals or reviewing answer quality.

## Procedure
1. Confirm required tools were used.
2. Confirm required skills were loaded.
3. Confirm every claim has citation ids.
4. Confirm probabilities are between 0 and 1.
5. Fail guarantee-style future claims unless clearly marked as refusal/abstention.
