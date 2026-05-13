# Agenten-Experte-SuiteCRM

Public SuiteCRM expert knowledge pack for A-KI program specialists.

This repository stores reproducible, versioned SuiteCRM knowledge artifacts used
by read-only specialist agents.

## Structure

```text
programs/
  suitecrm/
    raw/latest.md              # rendered crawl snapshot
    DOCS_INDEX.md              # generated page/topic index
    TOPIC_MAP.md               # CEO/Collector routing map
    RETRIEVAL.md               # read-only retrieval instructions
    SOURCE.md                  # source and license references
    profile.toml               # specialist profile
    state/source_state.json    # upstream state and crawl hash
scripts/
  crawl_docs_site.py           # reproducible docs-site crawler
  build_specialist_doc_pack.py # index/profile generator
  check_suitecrm_updates.py    # upstream change detector
```

## Source Model

The SuiteCRM specialist uses three layers:

- Official documentation: `SuiteCRM/SuiteDocs` and `https://docs.suitecrm.com/`
- Runtime/debug evidence: `SuiteCRM/SuiteCRM` and `SuiteCRM/SuiteCRM-Core`
- Local generated artifacts: crawl snapshot, topic map, retrieval guide and specialist profile

The generated knowledge pack is not an official SuiteCRM publication.

## Update Policy

The GitHub workflow `suitecrm-doc-sync.yml` runs roughly every two weeks.

It compares the stored SuiteDocs commit and docs-site fingerprint against the
current upstream state. If upstream changed, the workflow renews
`programs/suitecrm/raw/latest.md`, regenerates the SuiteCRM specialist artifacts
and opens a pull request.

## Licensing

SuiteCRM documentation content is licensed under the GNU Free Documentation
License 1.3 by the SuiteCRM/SuiteDocs project. See
`LICENSES/SuiteCRM-SuiteDocs-GFDL-1.3.md` and `NOTICE.md`.

A-KI helper scripts and repo-specific metadata are provided under the MIT
license unless they contain or derive from SuiteCRM documentation content. See
`LICENSES/A-KI-MIT.md`.
