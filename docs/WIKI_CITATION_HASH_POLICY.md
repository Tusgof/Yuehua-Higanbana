# Wiki Citation Hash Policy

## Rule

Every new preregistration that cites the local LLM Wiki must record the cited file's relative path and SHA-256 available at lock time. Its validator must reject a missing file, missing hash, or hash mismatch.

## Active Legacy Preregistrations

`experiments\active_wiki_citation_hashes.json` backfills the currently controlling H-A2 and H-G1 preregistrations without rewriting their locked or frozen content. Each entry binds:

- the preregistration path and its SHA-256;
- each cited wiki-relative path;
- the wiki file SHA-256 under `HIGANBANA_WIKI_ROOT`.

`scripts\audit_wiki_citation_hashes.py` verifies that registry in the state-audit tier. A changed preregistration or changed wiki source fails loudly until a reviewed replacement hash is recorded. This companion-registry exception is for active legacy artifacts; new preregistrations should embed `wiki_citation_hashes` directly.

## Historical Evidence

Old inactive preregistrations are not rewritten. Missing hashes on inactive artifacts are legacy warnings, not evidence that their current wiki contents equal the contents used originally.
