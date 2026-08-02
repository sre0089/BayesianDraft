# ADR-0002: Manual-First ESPN Integration

## Status

Accepted

## Context

The draft-day tool must remain reliable even if ESPN synchronization is unavailable, unstable, or legally constrained.

## Decision

Build manual draft entry, undo/redo, save/load, and correction workflows before ESPN synchronization.

## Consequences

The initial product can operate offline. ESPN sync can later reduce data-entry friction, but it must never be required for the draft room to function.
