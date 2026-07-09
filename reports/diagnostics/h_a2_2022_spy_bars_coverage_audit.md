# H-A2 2022 SPY Bars Acquisition/Import Tool

- **Mode**: `fixture`
- **Manifest status**: `fixture_tool_pass`
- **Coverage status**: `fixture_pass_real_data_not_imported`
- **Import status**: `fixture_import_pass`
- **Rows**: `8211`
- **Expected trading days**: `21`
- **Actual trading days**: `21`
- **Ready for exact H-A2 rerun**: `False`
- **Network used**: `False`
- **Paid data used**: `False`
- **IBKR historical request used**: `False`
- **Orders transmitted**: `False`

## Gates

| Gate | Pass |
|:--|:--:|
| `canonical_import_pass` | `True` |
| `coverage_audit_pass` | `True` |
| `timestamp_conversion_to_et_pass` | `True` |
| `orb_timestamp_coverage_pass` | `True` |
| `full_session_coverage_pass` | `True` |
| `join_to_existing_2022_10_option_quotes_pass` | `True` |
| `no_lookahead_timestamp_rule_documented` | `True` |
| `provenance_required_for_real_source` | `True` |
| `raw_hash_or_request_manifest_required_for_real_source` | `True` |
| `license_notes_required_for_real_source` | `True` |

## Next Safe Action

Rerun the IBKR readiness probe. Execute a live historical-bars request only after readiness is ready_for_manual_data_probe; then import real bars through this bounded shape and rerun coverage validation.
