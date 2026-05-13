#!/usr/bin/env python3
"""Build a compact program-specialist doc pack from a crawled markdown file.

The generated pack is intended for read-only expert agents. It keeps the raw
crawl as source of truth and creates lightweight routing/retrieval artifacts
that the CEO, Collector and specialist can use without loading the full crawl
on every run.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


TOC_RE = re.compile(
    r"^\s*(?P<num>\d+)\.\s+\[(?P<title>.+?)\]\(#seite-(?P<page>\d+)\)\s+-\s+`(?P<url>[^`]+)`\s*$"
)
PAGE_RE = re.compile(r"^## Seite (?P<page>\d+): (?P<title>.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Page:
    number: int
    title: str
    url: str
    line: int
    topic: str


TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "troubleshooting",
        (
            "troubleshooting",
            "debug",
            "logs",
            "possible issues",
            "support",
            "issue",
            "fehler",
        ),
    ),
    (
        "upgrade_migration",
        (
            "upgrade",
            "upgrading",
            "migration",
            "migrate",
            "legacy-migration",
            "manual migration",
            "releases",
        ),
    ),
    (
        "installation_operations",
        (
            "installation",
            "install",
            "webserver",
            "performance",
            "compatibility matrix",
            "cli installer",
            "ui installer",
        ),
    ),
    (
        "async_schedulers",
        (
            "scheduler",
            "schedulers",
            "async task",
            "messenger",
            "background",
            "cron",
        ),
    ),
    (
        "security_auth",
        (
            "oauth",
            "saml",
            "ldap",
            "login",
            "trusted hosts",
            "session",
            "authentication",
            "password",
        ),
    ),
    (
        "email_calendar",
        (
            "email",
            "inbound",
            "outbound",
            "calendar",
            "google suite",
            "microsoft",
        ),
    ),
    (
        "search_elasticsearch",
        (
            "elasticsearch",
            "search",
            "index",
        ),
    ),
    (
        "developer_api",
        (
            "/developer/api/",
            "api v",
            "json api",
            "postman",
            "api setup",
            "api methods",
        ),
    ),
    (
        "developer_extensions",
        (
            "/developer/extensions/",
            "architecture",
            "front-end",
            "frontend",
            "backend",
            "extension",
            "vardef",
            "process api",
            "save handler",
        ),
    ),
    (
        "admin_configuration",
        (
            "admin/",
            "administration panel",
            "configuration",
            "module management",
            "studio",
            "roles",
            "users",
        ),
    ),
    (
        "user_guides",
        (
            "/user/",
            "user guide",
            "using suitecrm",
        ),
    ),
)

TOPIC_TRIGGERS: dict[str, str] = {
    "troubleshooting": "errors, logs, failed upgrade, diagnostics, support",
    "upgrade_migration": "version upgrade, 7.x to 8.x migration, release changes, manual migration tasks",
    "installation_operations": "install, webserver, compatibility, performance, environment setup",
    "async_schedulers": "cron, schedulers, Symfony Messenger, async task workers, background jobs",
    "security_auth": "OAuth, SAML, LDAP, login throttling, sessions, trusted hosts",
    "email_calendar": "inbound/outbound email, OAuth mail provider, calendar sync, Microsoft/Google",
    "search_elasticsearch": "Elasticsearch setup, indexing, search troubleshooting",
    "developer_api": "API v4.1/v8, JSON API, Postman setup, API errors",
    "developer_extensions": "custom code, backend/frontend extensions, vardefs, process API, architecture",
    "admin_configuration": "admin panel, configuration, modules, users, roles, system settings",
    "user_guides": "end-user workflows and UI usage",
    "general": "general SuiteCRM docs and uncategorized topics",
}


def classify(title: str, url: str) -> str:
    haystack = f"{title} {url}".lower()
    for topic, needles in TOPIC_RULES:
        if any(needle in haystack for needle in needles):
            return topic
    return "general"


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_pages(text: str) -> list[Page]:
    toc: dict[int, tuple[str, str]] = {}
    for line in text.splitlines():
        match = TOC_RE.match(line)
        if match:
            page_num = int(match.group("page"))
            toc[page_num] = (match.group("title"), match.group("url"))

    pages: list[Page] = []
    for match in PAGE_RE.finditer(text):
        page_num = int(match.group("page"))
        fallback_title = match.group("title").strip()
        title, url = toc.get(page_num, (fallback_title, ""))
        topic = classify(title, url)
        pages.append(
            Page(
                number=page_num,
                title=title,
                url=url,
                line=line_for_offset(text, match.start()),
                topic=topic,
            )
        )

    return sorted(pages, key=lambda page: page.number)


def extract_header(text: str) -> list[str]:
    header = []
    for line in text.splitlines():
        if line.startswith("---"):
            break
        header.append(line)
    return header


def grouped_pages(pages: Iterable[Page]) -> dict[str, list[Page]]:
    grouped: dict[str, list[Page]] = {}
    for page in pages:
        grouped.setdefault(page.topic, []).append(page)
    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def write_source(
    out_dir: Path,
    source_ref: str,
    header: list[str],
    name: str,
    docs_repos: Sequence[str],
    code_repos: Sequence[str],
    issue_repos: Sequence[str],
) -> None:
    source_md = out_dir / "SOURCE.md"
    docs_lines = [f"- Docs repo: `{repo}`" for repo in docs_repos]
    code_lines = [f"- Code repo: `{repo}`" for repo in code_repos]
    issue_lines = [f"- Issue/PR search repo: `{repo}`" for repo in issue_repos]
    source_md.write_text(
        "\n".join(
            [
                f"# {name} Specialist Source",
                "",
                f"- Raw crawl: `{source_ref}`",
                "- Source of truth: official docs/source repositories where available; raw crawl is a dated snapshot and fallback.",
                "- Permission model: read-only specialist knowledge. Fixes are implemented by the Debugger, not by the specialist.",
                "",
                "## Repository Sources",
                "",
                *(docs_lines or ["- Docs repo: not configured"]),
                *(code_lines or ["- Code repo: not configured"]),
                *(issue_lines or ["- Issue/PR search repo: not configured"]),
                "",
                "## Crawl Header",
                "",
                *header,
                "",
            ]
        ),
        encoding="utf-8",
    )


def toml_list(values: Sequence[str]) -> str:
    return "[" + ", ".join(f'"{value}"' for value in values) + "]"


def repository_block(repo: str, role: str, use_for: Sequence[str]) -> str:
    return f'''[[repository_sources]]
id = "{repo}"
role = "{role}"
access = "READ_ONLY"
use_for = {toml_list(use_for)}
'''


def write_profile(
    out_dir: Path,
    slug: str,
    name: str,
    source_ref: str,
    docs_repos: Sequence[str],
    code_repos: Sequence[str],
    issue_repos: Sequence[str],
    repo_aliases: Sequence[str],
) -> None:
    profile = out_dir / "profile.toml"
    repository_sources: list[str] = []
    for repo in docs_repos:
        repository_sources.append(
            repository_block(
                repo,
                "official-documentation-source",
                ["canonical docs", "docs diff", "versioned source pages"],
            )
        )
    for repo in code_repos:
        repository_sources.append(
            repository_block(
                repo,
                "application-code-source",
                ["stacktrace lookup", "implementation evidence", "release/runtime behavior"],
            )
        )
    for repo in issue_repos:
        repository_sources.append(
            repository_block(
                repo,
                "live-debug-signal",
                ["open issues", "closed issues", "pull requests", "workarounds", "regressions"],
            )
        )

    profile.write_text(
        f'''id = "{slug}-specialist"
name = "{name} Specialist"
type = "program-specialist"
permissions = "READ_ONLY"
source_docs = ["{source_ref}"]
entrypoints = ["SOURCE.md", "DOCS_INDEX.md", "TOPIC_MAP.md", "RETRIEVAL.md"]
knowledge_layers = [
  "docs_rag: offizielle Dokumentation, Crawl-Snapshot, Parameter, Standardfehler, Installations- und Admin-Wege",
  "code_read: read-only Quellcode-Recherche fuer Stacktraces, Klassen, Services, Konfiguration und Versionsverhalten",
  "issue_pr_read: read-only GitHub-Issue-/PR-Recherche fuer neue, ungeloeste oder schlecht dokumentierte Bugs",
  "local_context: Logs, Collector-Snapshots und bisherige Debugger-Runs aus dem konkreten Issue"
]
repository_aliases = {toml_list(repo_aliases)}

{"".join(repository_sources)}

activation = """
Der CEO aktiviert diesen Spezialisten, wenn ein Issue nach zwei echten Debugger-Runs
nicht geloest ist und Hinweise auf {name}, CRM-Module, Admin-Konfiguration,
APIs, Authentifizierung, Scheduler, Migrationen, E-Mail, Suche oder Erweiterungen
enthaelt. Der Spezialist beantwortet Expertenfragen, nimmt aber keine Aenderungen
an Zielsystemen, Tickets, Dateien, Workflows oder Services vor.
"""

answer_contract = [
  "Kurzdiagnose",
  "Getrennte Evidenz: Doku, Code, Issues/PRs und lokaler Issue-Kontext",
  "Relevante Doku-Stellen mit Seitennummer/URL",
  "Relevante Code-/Issue-/PR-Treffer mit Repo, Pfad oder Link und Status",
  "Wahrscheinlichste Ursache",
  "Welche Evidenz fehlt noch",
  "Konkrete Checks fuer Collector oder Debugger",
  "Sicherer Fix-Pfad fuer den Debugger",
  "Risiken/Rollback-Hinweise",
  "Ob ein weiterer Spezialist benoetigt wird"
]

stop_rules = [
  "Keine Secrets oder personenbezogenen Rohdaten anfordern oder ausgeben",
  "Keine produktiven Aenderungen selbst ausfuehren",
  "Keine GitHub-Issues kommentieren, schliessen oder veraendern",
  "Keine Pull Requests oder Branches selbst erstellen",
  "Bei unklarer Version immer Versions-/Kompatibilitaetscheck fordern",
  "Bei Datenmigrationen immer Backup-, Staging- und Rollback-Frage markieren"
]
''',
        encoding="utf-8",
    )


def write_index(out_dir: Path, pages: list[Page], name: str) -> None:
    lines = [
        f"# {name} Docs Index",
        "",
        f"- Pages indexed: {len(pages)}",
        "- Use this file to select the smallest relevant document slice before reading the raw crawl.",
        "- Line numbers refer to the raw crawl listed in `SOURCE.md`.",
        "",
    ]

    for topic, topic_pages in grouped_pages(pages).items():
        lines.extend([f"## {topic}", ""])
        for page in topic_pages:
            url = f" - `{page.url}`" if page.url else ""
            lines.append(f"- Seite {page.number}, line {page.line}: {page.title}{url}")
        lines.append("")

    (out_dir / "DOCS_INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def write_topic_map(out_dir: Path, pages: list[Page], name: str) -> None:
    grouped = grouped_pages(pages)
    lines = [
        f"# {name} Topic Map",
        "",
        "Diese Topic Map ist das Routing-Werkzeug fuer CEO und Collector.",
        "",
        "| Topic | Pages | Activation terms |",
        "| --- | ---: | --- |",
    ]
    for topic, topic_pages in grouped.items():
        trigger = TOPIC_TRIGGERS.get(topic, "")
        lines.append(f"| `{topic}` | {len(topic_pages)} | {trigger} |")

    lines.extend(
        [
            "",
            "## Escalation Flow",
            "",
            "1. Debugger arbeitet zwei echte Runs autonom.",
            "2. Wenn nicht geloest: Debugger uebergibt komprimierte Lage an CEO.",
            "3. CEO waehlt passende Programmspezialisten ueber diese Topic Map.",
            "4. Spezialist antwortet nur lesend nach `answer_contract` aus `profile.toml`.",
            "5. Collector fuehrt Expertenantworten und Debug-Kontext zusammen.",
            "6. Debugger setzt den Fix direkt um und testet.",
            "",
        ]
    )
    (out_dir / "TOPIC_MAP.md").write_text("\n".join(lines), encoding="utf-8")


def write_retrieval(
    out_dir: Path,
    source_ref: str,
    name: str,
    code_repos: Sequence[str],
    issue_repos: Sequence[str],
) -> None:
    src = source_ref
    issue_search_lines = []
    for repo in issue_repos:
        issue_search_lines.extend(
            [
                f'gh issue list -R {repo} --state all --search "<stacktrace-or-error-fragment>"',
                f'gh pr list -R {repo} --state all --search "<class-or-error-fragment>"',
            ]
        )
    code_search_lines = []
    for repo in code_repos:
        safe_name = repo.replace("/", "_")
        code_search_lines.extend(
            [
                f"# Optional local mirror: .cache/repos/{safe_name}",
                f'rg -n "<class-or-method-or-error-fragment>" ".cache/repos/{safe_name}"',
            ]
        )

    lines = [
        f"# {name} Retrieval Guide",
        "",
        "Der Spezialist laedt zuerst `SOURCE.md`, `TOPIC_MAP.md` und `DOCS_INDEX.md`.",
        "Danach wird nur der relevante Ausschnitt aus dem Raw Crawl gelesen.",
        "",
        "## PowerShell Beispiele",
        "",
        "```powershell",
        f'rg -n "OAuth|Inbound Email|Microsoft" "{src}"',
        f'rg -n "Scheduler|cron|Messenger" "{src}"',
        f'rg -n "Logs and debugging|Possible Issues|Troubleshooting" "{src}"',
        "```",
        "",
        "Um eine Seite anhand der Line aus `DOCS_INDEX.md` zu lesen:",
        "",
        "```powershell",
        f'Get-Content -Path "{src}" | Select-Object -Skip 10125 -First 140',
        "```",
        "",
        "## GitHub Debugger-Erweiterung",
        "",
        "Bei Stacktraces, undokumentierten Fehlern oder Versionsregressionen reicht die Doku nicht. Dann werden Code, Issues und PRs read-only durchsucht.",
        "",
        "```powershell",
        *(code_search_lines or ["# Keine Code-Repositories konfiguriert"]),
        "```",
        "",
        "```powershell",
        *(issue_search_lines or ["# Keine Issue-Repositories konfiguriert"]),
        "```",
        "",
        "## Antwortdisziplin",
        "",
        "- Doku-, Code-, Issue-/PR- und lokalen Log-Kontext getrennt ausweisen.",
        "- Doku-Stellen immer mit Seite, Titel und URL nennen.",
        "- Issue-/PR-Treffer mit Repo, Titel, Status und Link nennen; keine Tickets veraendern.",
        "- Keine langen Doku-Passagen kopieren; nur kurze Evidenz und konkrete Diagnose.",
        "- Bei mehreren beteiligten Systemen weiteren Spezialisten vorschlagen, z.B. n8n, Docker, Caddy, PostgreSQL oder OAuth Provider.",
        "",
    ]
    (out_dir / "RETRIEVAL.md").write_text("\n".join(lines), encoding="utf-8")


def maybe_write_pages(out_dir: Path, source_text: str, pages: list[Page]) -> None:
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    matches = list(PAGE_RE.finditer(source_text))
    for idx, match in enumerate(matches):
        page_num = int(match.group("page"))
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(source_text)
        page = next((candidate for candidate in pages if candidate.number == page_num), None)
        if not page:
            continue
        filename = f"seite-{page_num:04d}.md"
        header = [
            f"# Seite {page.number}: {page.title}",
            "",
            f"- URL: `{page.url}`",
            f"- Source line: {page.line}",
            f"- Topic: `{page.topic}`",
            "",
        ]
        pages_dir.joinpath(filename).write_text(
            "\n".join(header) + source_text[start:end],
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Crawled markdown source file")
    parser.add_argument("--slug", required=True, help="Program slug, e.g. suitecrm")
    parser.add_argument("--name", required=True, help="Program display name, e.g. SuiteCRM")
    parser.add_argument(
        "--output-root",
        default=Path("agents") / "specialists",
        type=Path,
        help="Root directory for generated specialist packs",
    )
    parser.add_argument(
        "--emit-pages",
        action="store_true",
        help="Also split raw crawl into per-page markdown files. This can create many files.",
    )
    parser.add_argument(
        "--docs-repo",
        action="append",
        default=[],
        help="Official documentation repository, e.g. SuiteCRM/SuiteDocs. Can be repeated.",
    )
    parser.add_argument(
        "--code-repo",
        action="append",
        default=[],
        help="Application code repository for read-only debugging. Can be repeated.",
    )
    parser.add_argument(
        "--issue-repo",
        action="append",
        default=[],
        help="Repository whose issues/PRs should be searched for live debug signals. Can be repeated.",
    )
    parser.add_argument(
        "--repo-alias",
        action="append",
        default=[],
        help="Historical or redirect repository name to recognize in issues/docs. Can be repeated.",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.exists():
        raise SystemExit(f"Source file does not exist: {source}")
    try:
        source_ref = source.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        source_ref = source.as_posix()

    text = source.read_text(encoding="utf-8")
    pages = parse_pages(text)
    if not pages:
        raise SystemExit("No pages found. Expected headings like '## Seite 1: ...'.")

    out_dir = (args.output_root / args.slug).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    header = extract_header(text)
    issue_repos = args.issue_repo or args.code_repo
    write_source(out_dir, source_ref, header, args.name, args.docs_repo, args.code_repo, issue_repos)
    write_profile(
        out_dir,
        args.slug,
        args.name,
        source_ref,
        args.docs_repo,
        args.code_repo,
        issue_repos,
        args.repo_alias,
    )
    write_index(out_dir, pages, args.name)
    write_topic_map(out_dir, pages, args.name)
    write_retrieval(out_dir, source_ref, args.name, args.code_repo, issue_repos)
    if args.emit_pages:
        maybe_write_pages(out_dir, text, pages)

    print(f"Generated {args.name} specialist pack at {out_dir}")
    print(f"Indexed pages: {len(pages)}")
    print("Artifacts: SOURCE.md, profile.toml, DOCS_INDEX.md, TOPIC_MAP.md, RETRIEVAL.md")
    if args.emit_pages:
        print("Per-page files emitted under pages/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
