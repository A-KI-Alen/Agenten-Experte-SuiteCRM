# SuiteCRM Retrieval Guide

Der Spezialist laedt zuerst `SOURCE.md`, `TOPIC_MAP.md` und `DOCS_INDEX.md`.
Danach wird nur der relevante Ausschnitt aus dem Raw Crawl gelesen.

## PowerShell Beispiele

```powershell
rg -n "OAuth|Inbound Email|Microsoft" "programs/suitecrm/raw/latest.md"
rg -n "Scheduler|cron|Messenger" "programs/suitecrm/raw/latest.md"
rg -n "Logs and debugging|Possible Issues|Troubleshooting" "programs/suitecrm/raw/latest.md"
```

Um eine Seite anhand der Line aus `DOCS_INDEX.md` zu lesen:

```powershell
Get-Content -Path "programs/suitecrm/raw/latest.md" | Select-Object -Skip 10125 -First 140
```

## GitHub Debugger-Erweiterung

Bei Stacktraces, undokumentierten Fehlern oder Versionsregressionen reicht die Doku nicht. Dann werden Code, Issues und PRs read-only durchsucht.

```powershell
# Optional local mirror: .cache/repos/SuiteCRM_SuiteCRM
rg -n "<class-or-method-or-error-fragment>" ".cache/repos/SuiteCRM_SuiteCRM"
# Optional local mirror: .cache/repos/SuiteCRM_SuiteCRM-Core
rg -n "<class-or-method-or-error-fragment>" ".cache/repos/SuiteCRM_SuiteCRM-Core"
```

```powershell
gh issue list -R SuiteCRM/SuiteCRM --state all --search "<stacktrace-or-error-fragment>"
gh pr list -R SuiteCRM/SuiteCRM --state all --search "<class-or-error-fragment>"
gh issue list -R SuiteCRM/SuiteCRM-Core --state all --search "<stacktrace-or-error-fragment>"
gh pr list -R SuiteCRM/SuiteCRM-Core --state all --search "<class-or-error-fragment>"
```

## Antwortdisziplin

- Doku-, Code-, Issue-/PR- und lokalen Log-Kontext getrennt ausweisen.
- Doku-Stellen immer mit Seite, Titel und URL nennen.
- Issue-/PR-Treffer mit Repo, Titel, Status und Link nennen; keine Tickets veraendern.
- Keine langen Doku-Passagen kopieren; nur kurze Evidenz und konkrete Diagnose.
- Bei mehreren beteiligten Systemen weiteren Spezialisten vorschlagen, z.B. n8n, Docker, Caddy, PostgreSQL oder OAuth Provider.
