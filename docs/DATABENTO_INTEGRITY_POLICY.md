# Databento Paid-Artifact Integrity Policy

## Purpose

Container bytes alone are not sufficient to identify equivalent Databento DBN market records. Every paid `.dbn.zst` artifact therefore has two integrity identities:

1. `sha256`: SHA-256 of the original compressed container. This is immutable historical download evidence.
2. `canonical_content_sha256`: SHA-256 of the decompressed DBN record body after the metadata header. This identifies the encoded market records while excluding mutable DBN metadata and zstd envelope bytes.

The canonical record-body format is `dbn_record_body_after_metadata_v1`. It is not a replacement for the container hash.

## Verification Rule

- Matching container and canonical hashes: `pass`.
- Container hash differs but canonical record-body hash matches: `content_verified_envelope_variance`.
- Canonical record-body hash differs, is unavailable, or cannot be parsed: integrity failure.

`content_verified_envelope_variance` preserves the historical container hash and records a provider/header/container difference. It never edits or deletes that historical value.

For a disputed artifact, a sorted canonical record export may be computed as an additional diagnostic. It serializes all decoded records with deterministic column ordering and timestamps. This is used to confirm that record-body equality is semantically consistent; it is not required for routine full-tree verification.

## Operations

- `python scripts/verify_data_integrity.py` verifies both identities for all recorded paid artifacts.
- `python scripts/verify_data_integrity.py --write-supplemental-registry` records new download-report artifacts and refreshes canonical hashes for the raw Databento tree.
- `python scripts/verify_data_integrity.py --backfill-canonical-hashes` refreshes canonical hashes for the whole raw Databento tree without changing historical container hashes.

The local sidecar is `data/registry/paid_artifact_checksums.jsonl`. It is intentionally ignored by Git because it indexes local paid data. Committed diagnostics must state the file count, canonical format, outcome, and remaining blockers.

## 2024-06-13 Precedent

The two `oos_2024_06_intraday_exit_30m_chunk2` exit-check files had three distinct container hashes (historical, local, and one-time fresh provider re-download). On 2026-07-10, their decompressed DBN record-body hashes and sorted canonical record exports matched between the local and fresh copies. They are recorded as `content_verified_envelope_variance`.

The original historical containers are unavailable. This explains the present mismatch mechanism but cannot prove which metadata/container bytes were in the original historical file. The historical SHA-256 values remain unchanged.
