# REVIEW_PACKET

## 1. ENTRY POINT

Backend Entry: `main.py`

- The API server starts in `main.py` where the FastAPI app is created and the contract routes are registered.
- Requests enter through the FastAPI endpoints such as `POST /bucket/artifacts/write`, then flow through the validation layer before any storage write or read occurs.

## 2. CORE EXECUTION FLOW (MAX 3 FILES ONLY)

**File 1 — API Handler**  
Path: `main.py`  
What it does: Exposes the Core-facing contract endpoints and returns standardized success/error envelopes.

**File 2 — Validation Layer**  
Path: `validators/bucket_contract_validator.py`  
What it does: Enforces Core-only integration, payload-size checks, and lineage rules at the boundary.

**File 3 — Storage / Bucket Logic**  
Path: `services/append_only_storage.py`  
What it does: Stores artifacts append-only, computes server-side SHA256 hashes, and verifies chain integrity.

## 3. LIVE FLOW (REAL EXECUTION)

**User Action:** Core sends artifact write request.

**System Flow:** Core -> API -> Validation -> Append-only storage -> Response

**Request JSON (ACTUAL)**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "rp-003",
    "timestamp_utc": "2026-04-29T12:20:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "payload": {
      "message": "sample payload 3"
    }
  }
}
```

**Response JSON (ACTUAL)**

```json
{
  "success": true,
  "request_id": "6e2e33fe-ed9e-400b-953d-936aa12b309f",
  "timestamp": "2026-04-29T04:19:05.613591Z",
  "data": {
    "artifact_id": "rp-003",
    "hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42",
    "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "timestamp_utc": "2026-04-29T12:20:00Z",
    "storage_type": "append_only",
    "deterministic": true
  }
}
```

## 4. WHAT WAS BUILT IN THIS TASK

- APIs created / fixed: `/bucket/artifacts/write`, `/bucket/artifacts/read`, `/bucket/artifacts/query`, `/bucket/audit/read`.
- Validation rules added: Core-only `integration_id` enforcement, unknown-field rejection, payload-size enforcement, schema-version checks, and lineage validation.
- Contract enforcement added: Pydantic request models with `extra="forbid"`, standardized success/error envelopes, and boundary validation before storage.
- Integration readiness added: live API proof, Postman collection, audit logging, and file-based audit fallback when MongoDB is unavailable.

What was NOT touched:
- BHIV Core application code was not modified.
- The append-only storage model remained append-only; no delete/update behavior was added.

## 5. FAILURE CASES (MANDATORY)

### Case 1: Invalid schema

**Input — what was wrong:** `schema_version` was set to `"1.0"` instead of `"1.0.0"`.

**Input JSON**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "rp-bad-schema",
    "timestamp_utc": "2026-04-29T12:30:00Z",
    "schema_version": "1.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42",
    "payload": {
      "message": "bad schema"
    }
  }
}
```

**Output — real error response**

```json
{
  "success": false,
  "error": "Invalid schema version: 1.0. Expected: 1.0.0",
  "request_id": "2597811a-38d0-4d9b-8195-e248c7c47452",
  "timestamp": "2026-04-29T04:19:36.498365Z"
}
```

### Case 2: Unknown field

**Input — extra field present:** `extra_field` was added to the artifact envelope.

**Input JSON**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "rp-bad-field",
    "timestamp_utc": "2026-04-29T12:02:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42",
    "payload": {
      "message": "bad field"
    },
    "extra_field": "not allowed"
  }
}
```

**Output — real rejection**

```json
{
  "success": false,
  "error": "body -> artifact -> extra_field: Extra inputs are not permitted",
  "request_id": "6f095c99-a3ba-4050-b41a-764f03936feb",
  "timestamp": "2026-04-29T04:19:05.777852Z"
}
```

### Case 3: Invalid lineage / missing data

**Input — broken lineage:** `parent_hash` did not match the current chain tip.

**Input JSON**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "rp-bad-lineage",
    "timestamp_utc": "2026-04-29T12:03:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "invalid_parent_hash",
    "payload": {
      "message": "bad lineage"
    }
  }
}
```

**Output — real rejection**

```json
{
  "success": false,
  "error": "Invalid lineage: expected parent_hash=930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42",
  "request_id": "bd3b18f9-8147-4ff3-a841-b813ebfb4eb7",
  "timestamp": "2026-04-29T04:19:05.797883Z"
}
```

## 6. CONTRACT PROOF (CRITICAL)

### Write API

**Request (ACTUAL)**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "rp-003",
    "timestamp_utc": "2026-04-29T12:20:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "payload": {
      "message": "sample payload 3"
    }
  }
}
```

**Response (ACTUAL)**

```json
{
  "success": true,
  "request_id": "6e2e33fe-ed9e-400b-953d-936aa12b309f",
  "timestamp": "2026-04-29T04:19:05.613591Z",
  "data": {
    "artifact_id": "rp-003",
    "hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42",
    "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "timestamp_utc": "2026-04-29T12:20:00Z",
    "storage_type": "append_only",
    "deterministic": true
  }
}
```

Validation is enforced by `BucketArtifactsWriteRequest` plus `ensure_core_integration`, `ensure_payload_size_within_limit`, and `ensure_lineage_request_valid` before storage writes.

### Read API

**Request (ACTUAL)**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact_id": "rp-003"
}
```

**Response (ACTUAL)**

```json
{
  "success": true,
  "request_id": "001670c1-f476-4e69-888e-c49a75f79173",
  "timestamp": "2026-04-29T04:19:05.675719Z",
  "data": {
    "artifact": {
      "artifact_id": "rp-003",
      "timestamp_utc": "2026-04-29T12:20:00Z",
      "schema_version": "1.0.0",
      "source_module_id": "core_pipeline",
      "artifact_type": "integration_event",
      "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
      "payload": {
        "message": "sample payload 3"
      },
      "hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42"
    },
    "storage_type": "append_only",
    "chain_verified": true
  }
}
```

Validation is enforced by Core-only integration checks and storage lookup; the response also proves chain verification.

### Query API

**Request (ACTUAL)**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "limit": 20,
  "offset": 0,
  "artifact_type": "integration_event",
  "source_module_id": "core_pipeline"
}
```

**Response (ACTUAL)**

```json
{
  "success": true,
  "request_id": "21cfcf4c-f757-4d47-ae38-52d23ec4607a",
  "timestamp": "2026-04-29T04:19:05.705529Z",
  "data": {
    "artifacts": [
      {
        "artifact_id": "rp-003",
        "timestamp_utc": "2026-04-29T12:20:00Z",
        "schema_version": "1.0.0",
        "source_module_id": "core_pipeline",
        "artifact_type": "integration_event",
        "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
        "payload": {
          "message": "sample payload 3"
        },
        "hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42"
      }
    ],
    "count": 1,
    "total": 1,
    "limit": 20,
    "offset": 0,
    "filters": {
      "artifact_type": "integration_event",
      "source_module_id": "core_pipeline"
    },
    "storage_type": "append_only"
  }
}
```

Validation is enforced by Core-only integration checks plus deterministic metadata filtering and pagination.

## 7. CORE INTEGRATION PROOF

**Simulated BHIV Core write request (ACTUAL)**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact": {
    "artifact_id": "rp-003",
    "timestamp_utc": "2026-04-29T12:20:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "payload": {
      "message": "sample payload 3"
    }
  }
}
```

**Simulated BHIV Core read request (ACTUAL)**

```json
{
  "requester_id": "review_runner",
  "integration_id": "bhiv_core",
  "artifact_id": "rp-003"
}
```

**How Core will use this:** Core posts artifact envelopes to write data, then reads or queries by artifact ID and metadata for deterministic retrieval. The boundary rules keep malformed or unauthorized requests out of Bucket.

## 8. AUDIT / LOGGING PROOF

### One success log (ACTUAL)

From `/bucket/audit/read`:

```json
{
  "timestamp": "2026-04-29T04:19:05.613022",
  "operation_type": "CREATE",
  "artifact_id": "rp-003",
  "requester_id": "review_runner",
  "integration_id": "core_contract_api",
  "status": "success",
  "data_before": null,
  "data_after": {
    "artifact_id": "rp-003",
    "timestamp_utc": "2026-04-29T12:20:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "core_pipeline",
    "artifact_type": "integration_event",
    "parent_hash": "b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a",
    "payload": {
      "message": "sample payload 3"
    },
    "hash": "930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42"
  },
  "error_message": null,
  "immutable": true,
  "audit_version": "1.0",
  "_id": "file_0e6439cc2c764d26984f7b424094a8ba"
}
```

### One failure log (ACTUAL)

From `/bucket/audit/read`:

```json
{
  "timestamp": "2026-04-29T04:19:36.497868",
  "operation_type": "CREATE",
  "artifact_id": "rp-bad-schema",
  "requester_id": "review_runner",
  "integration_id": "core_contract_api",
  "status": "blocked",
  "data_before": null,
  "data_after": null,
  "error_message": "Invalid schema version: 1.0. Expected: 1.0.0",
  "immutable": true,
  "audit_version": "1.0",
  "_id": "file_bc0f8e39b47f4c00bfbbebc0439b9771"
}
```

**Where logs are stored:** The audit middleware writes to `data/audit.log` through the file-based fallback when MongoDB is not configured. The live server also exposed these logs through `/bucket/audit/read`.

## 9. PROOF OF EXECUTION

**Console / curl output (ACTUAL):**

```text
--- WRITE ---
{"success":true,"request_id":"6e2e33fe-ed9e-400b-953d-936aa12b309f","timestamp":"2026-04-29T04:19:05.613591Z","data":{"artifact_id":"rp-003","hash":"930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42","parent_hash":"b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a","timestamp_utc":"2026-04-29T12:20:00Z","storage_type":"append_only","deterministic":true}}
--- READ ---
{"success":true,"request_id":"001670c1-f476-4e69-888e-c49a75f79173","timestamp":"2026-04-29T04:19:05.675719Z","data":{"artifact":{"artifact_id":"rp-003","timestamp_utc":"2026-04-29T12:20:00Z","schema_version":"1.0.0","source_module_id":"core_pipeline","artifact_type":"integration_event","parent_hash":"b94a4a1c503810ccc19ac1c9e5ec103fb5038fd3a7295e5d004d8bdbf0d07b5a","payload":{"message":"sample payload 3"},"hash":"930a2e3e72916fa9b8d6c27e58406890761dd003cb27e881f40a41ed531b1d42"},"storage_type":"append_only","chain_verified":true}}
--- BAD_SCHEMA_REAL ---
{"success":false,"error":"Invalid schema version: 1.0. Expected: 1.0.0","request_id":"2597811a-38d0-4d9b-8195-e248c7c47452","timestamp":"2026-04-29T04:19:36.498365Z"}
```

## 10. FINAL SYSTEM TRUTH (IMPORTANT)

Bucket is an append-only artifact store that enforces a strict contract at the boundary before any data is written. It validates Core-only integration, schema version, payload size, and lineage, then computes the server-authoritative hash and stores artifacts immutably. Bucket does not execute payloads or make business decisions from payload content; the payload is treated as opaque data. Core must be the only caller because the contract and validation layer are designed around Core identifiers and deterministic replay. The audit trail captures both accepted and rejected operations for review and incident tracing.

ONE LINE TRUTH

This packet proves the live Core-to-Bucket execution path, real request/response pairs, rejection cases, and audit evidence needed to review the system in under two minutes.
