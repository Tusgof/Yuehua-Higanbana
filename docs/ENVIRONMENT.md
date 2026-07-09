# Higanbana Machine Environment

Machine-specific paths must not be committed into scripts, tests, or experiment artifacts.

Resolution order:

1. Environment variable.
2. Untracked `config/machine.json`.
3. Documented portable default.

| Purpose | Environment variable | `machine.json` key | Default |
|:--|:--|:--|:--|
| Local market-data tree | `HIGANBANA_DATA_ROOT` | `data_root` | `<repo>/data` |
| Local LLM Wiki | `HIGANBANA_WIKI_ROOT` | `wiki_root` | workspace-relative `LLM Wiki/LLM Wiki/wiki` |
| Python with IBKR packages | `HIGANBANA_IBKR_PYTHON` | `ibkr_python` | unset |

Create `config/machine.json` from `config/machine.example.json` when environment variables are inconvenient. Do not put API keys, passwords, tokens, or broker credentials in this file.

Experiment artifacts refer to external roots with tokens such as `${HIGANBANA_WIKI_ROOT}/concepts/...`. Runtime code resolves those tokens through `lib.environment`.
