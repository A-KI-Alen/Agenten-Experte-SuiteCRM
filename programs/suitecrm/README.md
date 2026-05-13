# SuiteCRM Specialist Knowledge Pack

This pack prepares SuiteCRM documentation and debug sources for an A-KI
read-only program specialist.

## Files

- `raw/latest.md`: current rendered crawl snapshot from `https://docs.suitecrm.com/`
- `DOCS_INDEX.md`: generated index with page number, source line, title and URL
- `TOPIC_MAP.md`: routing map for CEO and Collector
- `RETRIEVAL.md`: retrieval guide for docs, code, issues and PRs
- `SOURCE.md`: source references and crawl metadata
- `profile.toml`: specialist profile and answer contract
- `state/source_state.json`: upstream commit, crawl hash and check state

## Update Flow

1. Check `SuiteCRM/SuiteDocs` and the documentation site fingerprint.
2. If upstream changed, renew `raw/latest.md`.
3. Regenerate the specialist artifacts.
4. Open a pull request with the updated crawl and generated files.

The specialist remains read-only. Fixes are implemented by the A-KI Debugger.
