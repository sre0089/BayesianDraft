# ADR-0003: Simulation Reproducibility

## Status

Accepted

## Context

Recommendations, simulations, and audits must be explainable after the fact.

## Decision

All stochastic draft, availability, projection, and season simulations must accept explicit seeds and record those seeds in outputs and audit logs.

## Consequences

Results can be reproduced and debugged. APIs and schemas need to carry seed and model-version metadata from the beginning.
