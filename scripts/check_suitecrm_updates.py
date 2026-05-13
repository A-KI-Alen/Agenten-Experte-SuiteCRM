#!/usr/bin/env python3
"""Check whether the SuiteCRM documentation source changed upstream."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_STATE = Path("programs/suitecrm/state/source_state.json")
DEFAULT_REPORT = Path("reports/suitecrm-update-check.md")
SUITEDOCS_COMMIT_API = "https://api.github.com/repos/SuiteCRM/SuiteDocs/commits/master"
SITE_FINGERPRINT_URLS = (
    "https://docs.suitecrm.com/sitemap.xml",
    "https://docs.suitecrm.com/index.xml",
    "https://docs.suitecrm.com/",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_bytes(url: str) -> bytes:
    headers = {
        "User-Agent": "A-KI Program Knowledge Sync/1.0",
        "Accept": "application/json,text/xml,text/html,*/*",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return response.read()


def request_json(url: str) -> dict[str, Any]:
    return json.loads(request_bytes(url).decode("utf-8"))


def latest_suitedocs_commit() -> str:
    payload = request_json(SUITEDOCS_COMMIT_API)
    return payload["sha"]


def site_fingerprint() -> dict[str, str]:
    errors: list[str] = []
    for url in SITE_FINGERPRINT_URLS:
        try:
            body = request_bytes(url)
        except (HTTPError, URLError, TimeoutError) as exc:
            errors.append(f"{url}: {exc}")
            continue
        return {
            "site_fingerprint_url": url,
            "site_fingerprint_sha256": hashlib.sha256(body).hexdigest(),
        }
    raise RuntimeError("Could not fetch docs-site fingerprint: " + "; ".join(errors))


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def crawl_header_value(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^- \*\*{re.escape(label)}:\*\*\s*(.+)$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def refresh_state_from_crawl(
    state_path: Path,
    crawl_path: Path,
    latest_commit: str,
    fingerprint: dict[str, str],
) -> dict[str, Any]:
    state = load_state(state_path)
    crawl_text = crawl_path.read_text(encoding="utf-8")
    state.update(
        {
            "program": "suitecrm",
            "docs_url": "https://docs.suitecrm.com/",
            "docs_repo": "SuiteCRM/SuiteDocs",
            "docs_branch": "master",
            "suite_docs_commit": latest_commit,
            "crawl_file": crawl_path.as_posix(),
            "crawl_sha256": hashlib.sha256(crawl_path.read_bytes()).hexdigest(),
            "crawl_timestamp_utc": crawl_header_value(crawl_text, "Zeitstempel (UTC)") or utc_now(),
            "pages": int(crawl_header_value(crawl_text, "Seiten gecrawlt") or 0),
            "code_blocks": int(crawl_header_value(crawl_text, "Codebloecke erfasst") or 0),
            "last_checked_utc": utc_now(),
            **fingerprint,
        }
    )
    write_json(state_path, state)
    return state


def write_report(
    path: Path,
    state: dict[str, Any],
    latest_commit: str,
    fingerprint: dict[str, str],
    update_needed: bool,
    reasons: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SuiteCRM Docs Update Check",
        "",
        f"- Checked UTC: `{utc_now()}`",
        f"- Update needed: `{str(update_needed).lower()}`",
        f"- Stored SuiteDocs commit: `{state.get('suite_docs_commit', 'missing')}`",
        f"- Latest SuiteDocs commit: `{latest_commit}`",
        f"- Stored site fingerprint: `{state.get('site_fingerprint_sha256', 'missing')}`",
        f"- Latest site fingerprint: `{fingerprint.get('site_fingerprint_sha256', 'missing')}`",
        f"- Site fingerprint URL: `{fingerprint.get('site_fingerprint_url', 'missing')}`",
        "",
        "## Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in (reasons or ["No upstream changes detected."]))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_github_output(values: dict[str, str]) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--refresh-state-from-crawl",
        type=Path,
        help="Update state after a renewed crawl has been written.",
    )
    args = parser.parse_args()

    state = load_state(args.state)
    latest_commit = latest_suitedocs_commit()
    fingerprint = site_fingerprint()

    if args.refresh_state_from_crawl:
        state = refresh_state_from_crawl(
            args.state,
            args.refresh_state_from_crawl,
            latest_commit,
            fingerprint,
        )
        write_report(args.report, state, latest_commit, fingerprint, False, ["State refreshed from renewed crawl."])
        write_github_output({"update_needed": "false", "refreshed": "true"})
        return 0

    reasons: list[str] = []
    stored_commit = state.get("suite_docs_commit")
    if stored_commit and stored_commit != latest_commit:
        reasons.append("SuiteCRM/SuiteDocs commit changed.")

    stored_fingerprint = state.get("site_fingerprint_sha256")
    latest_fingerprint = fingerprint.get("site_fingerprint_sha256")
    if stored_fingerprint and stored_fingerprint != latest_fingerprint:
        reasons.append("Rendered docs-site fingerprint changed.")

    update_needed = bool(reasons)
    write_report(args.report, state, latest_commit, fingerprint, update_needed, reasons)
    write_github_output(
        {
            "update_needed": str(update_needed).lower(),
            "latest_commit": latest_commit,
            "stored_commit": str(stored_commit or ""),
        }
    )

    print(f"update_needed={str(update_needed).lower()}")
    for reason in reasons:
        print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
