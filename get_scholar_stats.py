import argparse
import json
import sys
from datetime import datetime, timezone
import re


def _configure_proxy(use_free_proxies: bool) -> None:
    if not use_free_proxies:
        return

    from scholarly import ProxyGenerator, scholarly

    proxy_generator = ProxyGenerator()
    if not proxy_generator.FreeProxies():
        raise RuntimeError("Failed to initialize free proxies")

    scholarly.use_proxy(proxy_generator)


_ARXIV_ID_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arXiv:\s*)(?P<id>(?:\d{4}\.\d{4,5}|[a-z\-]+/\d{7}))(?:v\d+)?",
    re.IGNORECASE,
)


def _json_sanitize(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_sanitize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    return str(value)


def _extract_arxiv_id_from_text(text: str) -> str:
    match = _ARXIV_ID_RE.search(text)
    if not match:
        return None
    return match.group("id")


def _extract_pub_arxiv_id(pub: dict) -> str:
    for key in ("pub_url", "eprint_url", "citedby_url", "url"):
        value = pub.get(key)
        if isinstance(value, str):
            arxiv_id = _extract_arxiv_id_from_text(value)
            if arxiv_id:
                return arxiv_id

    bib = pub.get("bib")
    if isinstance(bib, dict):
        for key in ("url", "eprint_url", "eprint", "abstract", "title"):
            value = bib.get(key)
            if isinstance(value, str):
                arxiv_id = _extract_arxiv_id_from_text(value)
                if arxiv_id:
                    return arxiv_id

    return None


def _extract_pub_citedby(pub: dict) -> int:
    for key in ("num_citations", "citedby", "citedby_total"):
        value = pub.get(key)
        if isinstance(value, int):
            return value
    return None


def _extract_pub_year(pub: dict) -> int:
    bib = pub.get("bib")
    if not isinstance(bib, dict):
        return None
    year = bib.get("pub_year") or bib.get("year")
    if isinstance(year, int):
        return year
    if isinstance(year, str):
        try:
            return int(year)
        except ValueError:
            return None
    return None


def _extract_pub_title(pub: dict) -> str:
    bib = pub.get("bib")
    if not isinstance(bib, dict):
        return None
    title = bib.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return None


def fetch_scholar_profile(
    user_id: str,
    name: str,
    use_free_proxies: bool,
    include_papers: bool,
    max_papers: int,
    sort_by: str,
) -> dict:
    _configure_proxy(use_free_proxies)

    from scholarly import scholarly

    if user_id:
        author = scholarly.search_author_id(user_id)
    else:
        if not name:
            raise ValueError("Either user_id or name must be provided")
        author = next(scholarly.search_author(name))

    sections = ["basics", "indices"]
    if include_papers and max_papers != 0:
        sections.append("publications")

    filled = scholarly.fill(author, sections=sections)

    citedby = filled.get("citedby") or filled.get("citedby_total")
    hindex = filled.get("hindex")
    hindex5y = filled.get("hindex5y")
    i10index = filled.get("i10index")
    i10index5y = filled.get("i10index5y")

    result: dict = {
        "scholar_id": filled.get("scholar_id") or user_id,
        "name": filled.get("name"),
        "affiliation": filled.get("affiliation"),
        "citedby": citedby,
        "hindex": hindex,
        "hindex5y": hindex5y,
        "i10index": i10index,
        "i10index5y": i10index5y,
    }

    if include_papers and max_papers != 0:
        publications = filled.get("publications") or []
        if not isinstance(publications, list):
            publications = []

        if max_papers > 0:
            publications = publications[:max_papers]

        papers: list[dict] = []
        for pub in publications:
            if not isinstance(pub, dict):
                continue

            try:
                pub_filled = scholarly.fill(pub)
            except Exception:
                pub_filled = pub

            bib = pub_filled.get("bib")
            if not isinstance(bib, dict):
                bib = {}

            arxiv_id = _extract_pub_arxiv_id(pub_filled)
            papers.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": _extract_pub_title(pub_filled),
                    "year": _extract_pub_year(pub_filled),
                    "citedby": _extract_pub_citedby(pub_filled),
                    "author_pub_id": pub_filled.get("author_pub_id"),
                    "pub_url": pub_filled.get("pub_url"),
                    "eprint_url": pub_filled.get("eprint_url"),
                    "citedby_url": pub_filled.get("citedby_url"),
                    "bib": bib,
                }
            )

        if sort_by == "citations":
            papers.sort(key=lambda p: (p.get("citedby") is None, -(p.get("citedby") or 0), p.get("title") or ""))
        elif sort_by == "year":
            papers.sort(key=lambda p: (p.get("year") is None, -(p.get("year") or 0), p.get("title") or ""))

        result["papers"] = papers

    return result


def build_author_pub_id_keyed_json(profile: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    papers = profile.get("papers") or []
    items: dict[str, dict] = {}
    unmatched: list[dict] = []

    if isinstance(papers, list):
        for paper in papers:
            if not isinstance(paper, dict):
                continue
            author_pub_id = paper.get("author_pub_id")
            if isinstance(author_pub_id, str) and author_pub_id.strip():
                items[author_pub_id] = _json_sanitize(paper)
            else:
                unmatched.append(_json_sanitize(paper))

    return {
        "generated_at": now,
        "scholar_id": profile.get("scholar_id"),
        "name": profile.get("name"),
        "affiliation": profile.get("affiliation"),
        "total_citations": profile.get("citedby"),
        "hindex": profile.get("hindex"),
        "hindex5y": profile.get("hindex5y"),
        "i10index": profile.get("i10index"),
        "i10index5y": profile.get("i10index5y"),
        "items": items,
        "unmatched_items": unmatched,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", default="vgcxKEcAAAAJ")
    parser.add_argument("--name", default="")
    parser.add_argument("--free-proxies", action="store_true")
    parser.add_argument("--no-papers", action="store_true")
    parser.add_argument("--max-papers", type=int, default=200)
    parser.add_argument("--sort", choices=["citations", "year", "none"], default="citations")
    parser.add_argument("--out", default="scholar_citations.json")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    include_papers = not args.no_papers
    sort_by = "" if args.sort == "none" else args.sort

    try:
        profile = fetch_scholar_profile(
            user_id=args.user_id or "",
            name=args.name or "",
            use_free_proxies=args.free_proxies,
            include_papers=include_papers,
            max_papers=args.max_papers,
            sort_by=sort_by,
        )
    except ModuleNotFoundError:
        print("Missing dependency: scholarly. Install with: pip install scholarly", file=sys.stderr)
        return 2
    except StopIteration:
        print("Author not found.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to fetch Scholar stats: {exc}", file=sys.stderr)
        return 1

    author_pub_id_keyed = build_author_pub_id_keyed_json(profile)
    try:
        with open(args.out, "w", encoding="utf-8") as f:
            if args.pretty:
                json.dump(author_pub_id_keyed, f, ensure_ascii=False, indent=2)
            else:
                json.dump(author_pub_id_keyed, f, ensure_ascii=False)
    except OSError as exc:
        print(f"Failed to write json file: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(author_pub_id_keyed, ensure_ascii=False))
        return 0

    print(f"name: {profile.get('name')}")
    print(f"scholar_id: {profile.get('scholar_id')}")
    print(f"affiliation: {profile.get('affiliation')}")
    print(f"citedby: {profile.get('citedby')}")
    print(f"hindex: {profile.get('hindex')}")
    print(f"hindex5y: {profile.get('hindex5y')}")
    print(f"i10index: {profile.get('i10index')}")
    print(f"i10index5y: {profile.get('i10index5y')}")

    papers = profile.get("papers") or []
    if include_papers and isinstance(papers, list):
        print("papers:")
        for paper in papers:
            if not isinstance(paper, dict):
                continue
            citedby = paper.get("citedby")
            year = paper.get("year")
            title = paper.get("title") or ""
            citedby_str = "" if citedby is None else str(citedby)
            year_str = "" if year is None else str(year)
            print(f"{citedby_str}\t{year_str}\t{title}")
    print(f"json_written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
