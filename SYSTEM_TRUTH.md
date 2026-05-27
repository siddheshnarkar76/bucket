# SYSTEM_TRUTH

Date: 2026-05-27

Bucket — System Truth Statement

Bucket IS:
- A deterministic artifact layer: artifacts are validated and stored with server-computed, deterministic SHA256 hashes over a canonical envelope representation.
- A truth anchor: the append-only log is the source-of-record for artifacts and provenance; it supports replay and verification.
- Append-only memory: writes are immutable; artifacts are never modified or deleted by normal operations.

Bucket IS NOT:
- An orchestrator: Bucket does not coordinate workflows, schedule tasks, or manage cross-system control flows.
- An intelligence engine: Bucket does not interpret payloads, make decisions, or apply business logic to artifact contents.
- An execution authority: Bucket does not execute or authorize actions for other systems.

Guarantees
- Immutability: once appended, artifacts remain unchanged and are tamper-evident via the hash chain.
- Deterministic hashing: server computes artifact hashes deterministically (canonical JSON sorting + separators) so replay yields identical hashes.
- Lineage integrity: each artifact optionally links to a `parent_hash`; Bucket enforces parent linkage to the current chain head.
- Replayability: the append-only log can be deterministically replayed to reconstruct system state for verification.

Operational constraints
- Schema is contractual: envelope validation forbids unknown top-level fields; contract changes require governance approval.
- Writes modify chain state (artifact_count, last_hash) — even test writes affect the append-only log and audit records.
- Production changes require staging verification, stakeholder signoff, and audit entries.

Evidence & artifacts
- Custody report: `BUCKET_CUSTODY_RECLAIM_REPORT.md`
- Contract guide: `MULTI_PRODUCT_CONTRACT_GUIDE.md`
- Trace continuity proof: `TRACE_CONTINUITY_PROOF.md`
- Truth & replay validation: `TRUTH_REPLAY_VALIDATION.md`

Responsible owners
- System owner: BHIV Core (Raj Prajapati)
- Testing & validation: Vinayak Tiwari
- Custody / handover: Soham Kotkar (temporary custodian)
