from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, BinaryIO


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def combined_named_file_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def dbn_section_hashes(stream: bytes, path: Path | None = None) -> dict[str, Any]:
    """Return separate hashes for a DBN metadata header and record body."""
    if len(stream) < 8:
        raise ValueError(f"{path or '<stream>'} is too short to contain a DBN metadata header.")
    metadata_length = int.from_bytes(stream[4:8], byteorder="little")
    body_offset = metadata_length + 8
    if body_offset > len(stream):
        raise ValueError(f"{path or '<stream>'} declares metadata beyond its decompressed length.")

    header = stream[:body_offset]
    body = stream[body_offset:]
    return {
        "total_decompressed_bytes": len(stream),
        "metadata_header_bytes": len(header),
        "metadata_header_sha256": hashlib.sha256(header).hexdigest(),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def dbn_record_body_hashes(path: Path) -> dict[str, Any]:
    """Hash a zstd-compressed DBN record body without loading it into memory."""
    with _zstd_open(path) as source:
        prefix = source.read(8)
        if len(prefix) < 8:
            raise ValueError(f"{path} is too short to contain a DBN metadata header.")
        metadata_length = int.from_bytes(prefix[4:8], byteorder="little")
        header_digest = hashlib.sha256(prefix)
        header_bytes = len(prefix)
        remaining_metadata = metadata_length
        while remaining_metadata:
            chunk = source.read(min(1024 * 1024, remaining_metadata))
            if not chunk:
                raise ValueError(f"{path} ended inside its DBN metadata header.")
            header_digest.update(chunk)
            header_bytes += len(chunk)
            remaining_metadata -= len(chunk)

        body_digest = hashlib.sha256()
        body_bytes = 0
        while chunk := source.read(1024 * 1024):
            body_digest.update(chunk)
            body_bytes += len(chunk)

    return {
        "total_decompressed_bytes": header_bytes + body_bytes,
        "metadata_header_bytes": header_bytes,
        "metadata_header_sha256": header_digest.hexdigest(),
        "bytes": body_bytes,
        "sha256": body_digest.hexdigest(),
    }


def _zstd_open(path: Path) -> BinaryIO:
    try:
        from compression import zstd
    except ModuleNotFoundError:
        try:
            import zstandard as zstd  # type: ignore[import-not-found]
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Canonical DBN hashing requires Python 3.14 compression.zstd or the optional zstandard package."
            ) from exc
    return zstd.open(path, "rb")
