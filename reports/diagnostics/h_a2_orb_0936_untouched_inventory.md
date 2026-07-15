# H-A2 ORB 09:36 Untouched Data Inventory

## ผลสรุป

- สถานะ: `local_untouched_dates_available`
- วันที่ local ทั้งหมด: `545`
- วันที่ untouched: `20`
- คำตัดสิน: `preregister_import_coverage_validation_before_outcomes`

## Regime ของข้อมูล Untouched

```json
{
  "macro": {
    "control": 20,
    "high_importance": 0,
    "unavailable": 0
  },
  "trend": {
    "downtrend": 0,
    "unclassified": 20,
    "uptrend": 0
  },
  "vix": {
    "low": 0,
    "normal": 20,
    "out_of_scope": 0,
    "unavailable": 0
  }
}
```

## ความเพียงพอของข้อมูล

```json
{
  "exact_mintrl_status": "unknown_until_valid_timestamp_correct_returns_exist",
  "idealized_planning_scenarios": [
    {
      "idealized_mintrl": 46,
      "null_sharpe": 0.0,
      "observed_sharpe": 0.25
    },
    {
      "idealized_mintrl": 14,
      "null_sharpe": 0.0,
      "observed_sharpe": 0.5
    },
    {
      "idealized_mintrl": 8,
      "null_sharpe": 0.0,
      "observed_sharpe": 0.75
    },
    {
      "idealized_mintrl": 6,
      "null_sharpe": 0.0,
      "observed_sharpe": 1.0
    },
    {
      "idealized_mintrl": 57,
      "null_sharpe": 0.5,
      "observed_sharpe": 0.75
    },
    {
      "idealized_mintrl": 18,
      "null_sharpe": 0.5,
      "observed_sharpe": 1.0
    }
  ],
  "raw_inventory_sufficient_for_import_preregistration": true,
  "reason": "Untouched raw dates are available, but coverage and target outcomes remain unread until a separate import/validation preregistration passes.",
  "validation_ready": false
}
```

## Timestamp และ Integrity

```json
{
  "coverage_policy": {
    "availability": "A date must have SPY bars, complete two-leg 0DTE quotes at or after 09:37, and 15:45 close quotes.",
    "current_coverage_result": "raw_files_present_but_quote_and_bar_coverage_requires_separate_preregistration",
    "integrity": "Every paid raw artifact must have container and canonical-content SHA-256 metadata and pass full verification before a future run.",
    "timestamp": "Signal 09:36 <= decision 09:36 <= first eligible entry quote 09:37."
  },
  "integrity_metadata": {
    "date_named_raw_file_count": 6672,
    "dual_hash_metadata_count": 6672,
    "missing_registry_paths": [],
    "note": "This inventory checks committed checksum metadata only. The fixture/full integrity verification re-hashes file content.",
    "registered_file_count": 6672,
    "registry_path": "D:\\Fogust\\Workspace\\Investment\\Project\\SPY 0DTE - Higanbana\\data\\registry\\paid_artifact_checksums.jsonl",
    "status": "pass"
  }
}
```

## ข้อห้าม

รายงานนี้อ่านเฉพาะ metadata/provenance และไม่ parse target-day PnL หรือ option outcomes จึงไม่ใช่ผลทดลองและไม่ต้องเขียน research log
