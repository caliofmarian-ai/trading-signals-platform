# DOCUMENT STATUS POLICY

This document defines the official lifecycle status of documents in the BinaryBot repository.

## Status Types

### ACTIVE
The document reflects the current implementation and must be kept synchronized with code.

### PARTIAL
The document describes the intended architecture but implementation is incomplete.

### LEGACY
The document describes deprecated architecture or replaced components.

### ARCHIVED
Historical document preserved for reference only.

## Governance Rules

1. Every architecture document must contain a **Status** section.
2. Status must be one of: ACTIVE / PARTIAL / LEGACY / ARCHIVED.
3. Code changes affecting architecture must update corresponding documents.
4. Legacy documents should not be deleted — they should be marked LEGACY.
5. The implementation matrix must be updated when major modules change.

## Repository Responsibility

Maintaining documentation integrity is required for:

- Architecture clarity
- Future contributors
- AI-assisted development
- Operational audits
