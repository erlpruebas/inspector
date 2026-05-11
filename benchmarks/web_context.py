from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


USER_AGENT = "ai-arena-web-context/1.0"


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    excerpt: str = ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a small web context packet for benchmark tasks.")
    parser.add_argument("query")
    parser.add_argument("--output", default="")
    parser.add_argument("--max-results", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = search_web(args.query, max_results=args.max_results)
    if args.json:
        text = json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2)
    else:
        text = format_web_context(args.query, results)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


def build_web_context(prompt: str, max_results: int | None = None) -> str:
    query = prompt_to_query(prompt)
    results = search_web(query, max_results=max_results or int(os.getenv("BENCH_WEB_MAX_RESULTS", "4")))
    return format_web_context(query, results)


def prompt_to_query(prompt: str) -> str:
    for line in prompt.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    compact = " ".join(prompt.split())
    return compact[:180]


def search_web(query: str, max_results: int = 4) -> list[SearchResult]:
    results = duckduckgo_html_search(query, max_results=max_results)
    enriched: list[SearchResult] = []
    for result in results:
        excerpt = fetch_page_excerpt(result.url)
        enriched.append(SearchResult(result.title, result.url, result.snippet, excerpt))
    return enriched


def duckduckgo_html_search(query: str, max_results: int = 4) -> list[SearchResult]:
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    raw = fetch_text(url)
    items: list[SearchResult] = []
    pattern = re.compile(
        r'<a rel="nofollow" class="result__a" href="(?P<href>.*?)".*?>(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
        flags=re.DOTALL,
    )
    for match in pattern.finditer(raw):
        href = decode_duckduckgo_url(clean_html(match.group("href")))
        title = clean_html(match.group("title"))
        snippet = clean_html(match.group("snippet"))
        if href and title:
            items.append(SearchResult(title, href, snippet))
        if len(items) >= max_results:
            break
    return items


def fetch_page_excerpt(url: str, limit: int = 1400) -> str:
    try:
        text = fetch_text(url, timeout=12)
    except Exception as exc:
        return f"[no se pudo leer la pagina: {type(exc).__name__}]"
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", text)
    text = clean_html(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def fetch_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        charset = response.headers.get_content_charset()
        if charset:
            decoded = body.decode(charset, errors="replace")
            if "Ã" not in decoded and "ï¿½" not in decoded:
                return decoded
        return body.decode("utf-8", errors="replace")


def clean_html(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    return fix_mojibake(re.sub(r"\s+", " ", value).strip())


def fix_mojibake(value: str) -> str:
    if "Ã" not in value and "Â" not in value and "ï¿½" not in value:
        return value
    for encoding in ("latin1", "cp1252"):
        try:
            repaired = value.encode(encoding, errors="ignore").decode("utf-8", errors="ignore")
        except UnicodeError:
            continue
        if repaired and repaired.count("Ã") < value.count("Ã"):
            return repaired
    return value


def decode_duckduckgo_url(value: str) -> str:
    if value.startswith("//duckduckgo.com/l/?"):
        value = "https:" + value
    parsed = urllib.parse.urlparse(value)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query:
        return query["uddg"][0]
    return value


def format_web_context(query: str, results: list[SearchResult]) -> str:
    lines = [
        "# Web context",
        "",
        f"Consulta preparada por el benchmark: {query}",
        "",
        "Usa estas fuentes como contexto. Si la tarea pide datos actuales, cita la fuente y la fecha de consulta.",
        "",
    ]
    if not results:
        lines.append("No se encontraron resultados web automaticamente.")
        return "\n".join(lines).strip() + "\n"
    for index, item in enumerate(results, start=1):
        lines.extend(
            [
                f"## Fuente {index}: {item.title}",
                f"URL: {item.url}",
                f"Resumen buscador: {item.snippet or '[sin resumen]'}",
                f"Extracto: {item.excerpt or '[sin extracto]'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
