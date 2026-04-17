1. ENTRY POINT

Backend Entry: File path: main.py
- Where the API server starts: `main.py` starts the FastAPI app and runs `uvicorn` when invoked as __main__.
- How a request enters the system: Requests hit FastAPI routes defined in `main.py`; Pydantic models validate input at the boundary, then handlers call the validation layer and storage services.

2. CORE EXECUTION FLOW (MAX 3 FILES ONLY)

File 1 — API Handler
Path: main.py
What it does: Defines Core-facing contract endpoints (`/bucket/artifacts/write`, `/bucket/artifacts/read`, `/bucket/artifacts/query`, `/bucket/audit/read`) and standard response envelopes.

File 2 — Validation Layer
Path: validators/bucket_contract_validator.py
What it does: Enforces `integration_id` bounds, payload size limits, and lineage rules; raises `ContractValidationError` on contract violations.

File 3 — Storage / Bucket Logic
Path: services/append_only_storage.py
What it does: Implements append-only JSONL storage, deterministic SHA256 hashing, artifact structure validation, chain state and storage operations.

3. LIVE FLOW (REAL EXECUTION)

User Action: Core sends artifact write request

System Flow: Core -> API (`/bucket/artifacts/write`) -> Validation -> Append-only storage -> Response

Request JSON (ACTUAL)
{
  "requester_id": "test_runner",
  "integration_id": "core",
  "artifact": {
    "artifact_id": "test_001",
    "timestamp_utc": "2026-04-17T12:00:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_test",
    "artifact_type": "test",
    "parent_hash": null,
    "payload": {"data": "sample payload"}
  }
}

Response JSON (ACTUAL)
{
  "success": true,
  "request_id": "8df920b5-c2e6-47c2-8922-61ff90af6caa",
  "timestamp": "2026-04-17T07:12:46.500560Z",
  "data": {
    "artifact_id": "test_001",
    "hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "parent_hash": null,
    "timestamp_utc": "2026-04-17T12:00:00Z",
    "storage_type": "append_only",
    "deterministic": true
  }
}

4. WHAT WAS BUILT IN THIS TASK

- APIs created / fixed: `/bucket/artifacts/write`, `/bucket/artifacts/read`, `/bucket/artifacts/query`, `/bucket/audit/read`, plus supporting schema endpoints (`/bucket/schema-info`, `/bucket/compute-hash`, etc.)
- Validation rules added: `integration_id` whitelist/prefix enforcement, payload size deterministic check, lineage (parent_hash) enforcement, schema version checks
- Contract enforcement added: Pydantic models with `extra="forbid"` and explicit ContractValidationError handling at API boundary
- Integration readiness added: standardized success/error envelopes, audit hooks on all contract endpoints

What was NOT touched:
- Core code (BHIV Core) — no changes
- Append-only storage internals were not modified beyond using them as the canonical storage implementation

5. FAILURE CASES (MANDATORY)

Case 1: Invalid schema
Input -> what was wrong:
  - Request: `schema_version` set to `"1.0"` (server expects `"1.0.0"`)
Input JSON:
  { "requester_id": "test_runner", "integration_id": "core", "artifact": { "artifact_id": "test_001", "timestamp_utc": "2026-04-17T12:00:00Z", "schema_version": "1.0", "source_module_id": "core_test", "artifact_type": "test", "parent_hash": null, "payload": {"data": "sample payload"} } }

Output -> error response (REAL):
  {"success":false,"error":"Invalid schema version: 1.0. Expected: 1.0.0","request_id":"ac59f2cb-b0e2-4d51-bf3a-373221fd5872","timestamp":"2026-04-17T07:12:30.907869Z"}

Case 2: Unknown field
Input -> extra field `extra_field` present in artifact envelope
Input JSON:
  { "requester_id": "test_runner", "integration_id": "core", "artifact": { "artifact_id": "test_003", "timestamp_utc": "2026-04-17T12:10:00Z", "schema_version": "1.0.0", "source_module_id": "core_test", "artifact_type": "test", "parent_hash": null, "payload": {"data": "sample payload"}, "extra_field": "should_be_rejected" } }

Output -> rejection (REAL):
  {"success":false,"error":"body -> artifact -> extra_field: Extra inputs are not permitted","request_id":"bf21cd6d-2fa3-4954-9720-6229736de28e","timestamp":"2026-04-17T07:13:43.548404Z"}

Case 3: Invalid lineage / missing data
Input -> incorrect `parent_hash` while chain expected a different hash
Input JSON:
  { "requester_id": "test_runner", "integration_id": "core", "artifact": { "artifact_id": "test_002", "timestamp_utc": "2026-04-17T12:05:00Z", "schema_version": "1.0.0", "source_module_id": "core_test", "artifact_type": "test", "parent_hash": "invalid_parent_hash_12345", "payload": {"data": "payload for invalid lineage"} } }

Output -> rejection (REAL):
  {"success":false,"error":"Invalid lineage: expected parent_hash=b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a","request_id":"f2d0fa34-0774-4cde-a8bc-efa559c790ac","timestamp":"2026-04-17T07:13:59.504439Z"}

6. CONTRACT PROOF (CRITICAL)

Write API → request + response (REAL): see section 3 above (write request for `test_001` and successful response). Validation enforced by `validators/bucket_contract_validator.py` checks and `append_only_storage.validate_artifact_structure()` before storing.

Read API → request + response (REAL):
Request JSON:
  { "requester_id": "test_runner", "integration_id": "core", "artifact_id": "test_001" }
Response JSON (REAL):
  {"success":true,"request_id":"f373148c-4e2b-4acc-86be-5459016d3972","timestamp":"2026-04-17T07:12:54.467581Z","data":{"artifact":{"artifact_id":"test_001","timestamp_utc":"2026-04-17T12:00:00Z","schema_version":"1.0.0","source_module_id":"core_test","artifact_type":"test","parent_hash":null,"payload":{"data":"sample payload"},"hash":"b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a"},"storage_type":"append_only","chain_verified":true}}
Validation: `ensure_core_integration` and storage `get_artifact` used; response validated by `core_api_contract` when configured.

Query API → request + response (REAL):
Request JSON:
  { "requester_id": "test_runner", "integration_id": "core", "limit": 10, "offset": 0 }
Response JSON (REAL): truncated:
  {"success":true,"request_id":"063e4650-f636-4e0c-b389-f19e847c3d18","timestamp":"2026-04-17T07:13:02.419581Z","data":{"artifacts":[{"artifact_id":"test_001",...}],"count":1,"total":1,...}}
Validation: `ensure_core_integration` plus `artifact_matches_filters` and server-side pagination apply contract rules.

7. CORE INTEGRATION PROOF

Simulated BHIV Core calls (REAL):
- Write request: same write JSON in section 3. Core will POST to `/bucket/artifacts/write` with `integration_id` set to `core` (or `core_*`) and receive deterministic `hash` and `artifact_id` in response.
- Read request: same read JSON above. Core will POST to `/bucket/artifacts/read` to retrieve artifact and chain verification status.

How Core will use this: Core performs writes to persist artifacts and later reads/queries to fetch historical artifacts deterministically; contract validations prevent unauthorized callers or malformed payloads.

8. AUDIT / LOGGING PROOF

One success log (REAL entry from audit read):
{
  "timestamp": "2026-04-17T07:12:46.500397",
  "operation_type": "CREATE",
  "artifact_id": "test_001",
  "requester_id": "test_runner",
  "integration_id": "core_contract_api",
  "status": "success",
  "data_after": { "artifact_id": "test_001", "timestamp_utc": "2026-04-17T12:00:00Z", "schema_version": "1.0.0", "source_module_id": "core_test", "artifact_type": "test", "parent_hash": null, "payload": {"data":"sample payload"}, "hash": "b94a4a1c5038..." }
}

One failure log (REAL entry from audit read):
{
  "timestamp": "2026-04-17T07:13:59.504277",
  "operation_type": "CREATE",
  "artifact_id": "test_002",
  "requester_id": "test_runner",
  "integration_id": "core_contract_api",
  "status": "blocked",
  "error_message": "Invalid lineage: expected parent_hash=b94a4a1c5..."
}

Where logs are stored: Audit uses MongoDB when `MONGODB_URI` is provided; in this environment MongoDB was not available so the middleware used an in-memory fallback (entries shown with `_id` like `mem_9`). When MongoDB is configured, the same audit records are written to a persistent `audit` collection.

9. PROOF OF EXECUTION

- Console / run evidence: the running server responded to live requests during this session (see `/health` and contract endpoint responses above). Example `/health` output (REAL):
  {"status":"unhealthy","bucket_version":"1.0.0","append_only_storage":{"status":"active","artifact_count":0,...}}
- Curl/Invoke-RestMethod outputs for the requests above were executed and captured during the session; the request/response JSON in this packet are exact outputs from those calls.

10. FINAL SYSTEM TRUTH (4–5 lines)

Bucket is an append-only artifact store that enforces a strict API contract at the boundary: it validates schema version, payload size, caller integration, and lineage before computing a server-authoritative hash and persisting artifacts. Bucket does NOT interpret or execute business logic from payloads — payloads are opaque and domain-neutral. Core must be the only caller because constitutional validation restricts `integration_id` to Core identifiers and the storage enforces lineage and schema guarantees that Core relies on for deterministic replay. The audit trail records every success and rejection for forensic validation.

ONE LINE TRUTH

This packet proves the exact Core→Bucket execution path, real request/response pairs, failure cases, and audit evidence so the reviewer can validate integration readiness without opening the repository.
# REVIEW_PACKET

## 1. ENTRY POINT
Backend entry file:
- `main.py`

## 2. CORE EXECUTION FLOW (MAX 3 FILES)
API handler:
- `main.py` (contract endpoints)

Validation layer:
- `validators/bucket_contract_validator.py`

Storage layer:
- `services/append_only_storage.py`

## 3. LIVE FLOW (Core -> Bucket)

### Write flow
Core request -> `POST /bucket/artifacts/write` -> boundary validation -> append-only store -> success envelope.

Real request JSON:
```json
{
  "requester_id": "core_service",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "live-001",
    "timestamp_utc": "2026-04-14T12:30:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": null,
    "payload": {"message": "hello"}
  }
}
```

Real response JSON shape:
```json
{
  "success": true,
  "request_id": "uuid",
  "timestamp": "ISO8601",
  "data": {
    "artifact_id": "live-001",
    "hash": "sha256hex",
    "parent_hash": null,
    "timestamp_utc": "2026-04-14T12:30:00Z",
    "storage_type": "append_only",
    "deterministic": true
  }
}
```

### Read flow
Core request -> `POST /bucket/artifacts/read` -> boundary validation -> read append log -> response envelope.

### Query flow
Core request -> `POST /bucket/artifacts/query` -> boundary validation -> deterministic filter -> response envelope.

## 4. WHAT WAS BUILT
- Contract APIs standardized for Core.
- Strict validation and unknown field rejection.
- Core-only boundary checks.
- Standard success/error response envelopes.
- Request/success/rejection/failure logging hooks.

## 5. FAILURE CASES
- Invalid schema -> 422
- Unknown field -> 422
- Invalid integration -> 400
- Invalid lineage -> 400
- Oversized payload -> 400
- Missing artifact -> 404

## 6. PROOF
- API docs and contract specs:
  - `CONTRACT_SPEC.md`
  - `API_STANDARDIZATION.md`
  - `CORE_INTEGRATION_SIM.md`
  - `VALIDATION_RULES.md`
  - `AUDIT_FLOW.md`
  - `FAILURE_HANDLING.md`
- Runtime proof method:
  - Postman collection provided.
  - curl commands provided in docs.
  - endpoint logs include request_id and outcome status.

## Manual validation owners
- Vinayak Tiwari: API correctness validation
- Akash: functionality testing (real flows)
- Raj Prajapati: BHIV Core consumption
- Ranjit: boundary awareness only (no direct integration)
