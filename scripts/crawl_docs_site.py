#!/usr/bin/env python3
"""Crawl a same-origin documentation site and write one combined markdown file."""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown


SKIP_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".ico",
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".zip",
    ".tar",
    ".gz",
)


@dataclass(frozen=True)
class PageResult:
    url: str
    title: str
    markdown: str
    depth: int


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    clean, _fragment = urldefrag(url)
    parsed = urlparse(clean)
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return parsed._replace(path=path, query="").geturl()


def valid_url(url: str, base_netloc: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc != base_netloc:
        return False
    return not parsed.path.lower().endswith(SKIP_EXTENSIONS)


def content_node(soup: BeautifulSoup) -> BeautifulSoup:
    for selector in ("main", "article", ".td-content", ".content", "#content"):
        node = soup.select_one(selector)
        if node:
            return node
    return soup.body or soup


def clean_node(node: BeautifulSoup) -> BeautifulSoup:
    for removable in node.select("script, style, nav, header, footer, aside, form"):
        removable.decompose()
    return node


def page_title(soup: BeautifulSoup, fallback_url: str) -> str:
    heading = soup.find(["h1", "h2"])
    if heading and heading.get_text(strip=True):
        return heading.get_text(" ", strip=True)
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return fallback_url


def extract_links(soup: BeautifulSoup, url: str, base_netloc: str) -> list[str]:
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        target = normalize_url(urljoin(url, href))
        if valid_url(target, base_netloc):
            links.add(target)
    return sorted(links)


def fetch_page(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def crawl(start_url: str, max_pages: int, max_depth: int) -> list[PageResult]:
    normalized_start = normalize_url(start_url)
    base_netloc = urlparse(normalized_start).netloc
    session = requests.Session()
    session.headers.update({"User-Agent": "A-KI Agenten-Experte-SuiteCRM Crawler/1.0"})

    queue: deque[tuple[str, int]] = deque([(normalized_start, 0)])
    seen: set[str] = set()
    results: list[PageResult] = []

    while queue and len(results) < max_pages:
        url, depth = queue.popleft()
        if url in seen or depth > max_depth:
            continue
        seen.add(url)

        try:
            soup = fetch_page(session, url)
        except requests.RequestException as exc:
            print(f"skip {url}: {exc}")
            continue

        title = page_title(soup, url)
        node = clean_node(content_node(soup))
        markdown = html_to_markdown(str(node), heading_style="ATX").strip()
        results.append(PageResult(url=url, title=title, markdown=markdown, depth=depth))

        if depth < max_depth:
            for link in extract_links(soup, url, base_netloc):
                if link not in seen:
                    queue.append((link, depth + 1))

        print(f"crawled {len(results)}/{max_pages}: {url}")

    return results


def anchor(title: str, page_number: int) -> str:
    return f"seite-{page_number}"


def code_block_count(markdown: str) -> int:
    return len(re.findall(r"```", markdown)) // 2


def write_combined(start_url: str, pages: list[PageResult], output: Path) -> None:
    combined_body = "\n\n".join(page.markdown for page in pages)
    code_blocks = code_block_count(combined_body)
    lines = [
        f"# Documentation Crawl: {start_url}",
        "",
        f"- **Start-URL:** {start_url}",
        f"- **Seiten gecrawlt:** {len(pages)}",
        f"- **Codebloecke erfasst:** {code_blocks}",
        "- **Tabs/Accordions aktiviert:** 0",
        f"- **Zeitstempel (UTC):** {utc_now()}",
        "- **Erfassungsmodus:** Requests/BeautifulSoup Same-Origin Crawl, Markdownify Rendering",
        "",
        "---",
        "",
        "## Inhaltsverzeichnis",
        "",
    ]

    for index, page in enumerate(pages, start=1):
        lines.append(f"{index}. [{page.title}](#{anchor(page.title, index)}) - `{page.url}`")

    for index, page in enumerate(pages, start=1):
        lines.extend(
            [
                "",
                "---",
                "",
                f"## Seite {index}: {page.title}",
                "",
                f"- **URL:** `{page.url}`",
                f"- **Depth:** {page.depth}",
                f"- **Content SHA256:** `{hashlib.sha256(page.markdown.encode('utf-8')).hexdigest()}`",
                "",
                page.markdown,
            ]
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-url", default="https://docs.suitecrm.com/")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pages", type=int, default=700)
    parser.add_argument("--max-depth", type=int, default=8)
    args = parser.parse_args()

    pages = crawl(args.start_url, args.max_pages, args.max_depth)
    if not pages:
        raise SystemExit("No pages crawled.")
    write_combined(args.start_url, pages, args.output)
    print(f"wrote {args.output} with {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
