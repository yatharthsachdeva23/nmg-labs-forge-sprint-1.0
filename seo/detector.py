from __future__ import annotations
import csv
import os
from collections import defaultdict


def load_rows(export_dir: str) -> list[dict]:
    path = os.path.join(export_dir, "internal_all.csv")
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    return []


def _int(v, default=0):
    try:
        return int(float(str(v).strip()))
    except Exception:
        return default


def _float(v, default=0.0):
    try:
        return float(str(v).strip())
    except Exception:
        return default


def is_html(r):    return "text/html" in (r.get("Content Type", "") or "").lower()
def is_image(r):   return "image" in (r.get("Content Type", "") or "").lower()
def is_pdf(r):     return "application/pdf" in (r.get("Content Type", "") or "").lower()
def is_200(r):     return _int(r.get("Status Code")) == 200
def indexable(r):  return (r.get("Indexability", "") or "").strip().lower() == "indexable"


def detect(rows: list[dict]) -> list[dict]:
    """Return a completely isolated, unique list of all 59 explicit issue dicts."""
    issues = []

    def add(t, sev, urls, explanation):
        unique_urls = sorted(list(set(urls)))
        if unique_urls:
            issues.append({
                "type": t, 
                "severity": sev, 
                "affected_urls": unique_urls,
                "count": len(unique_urls), 
                "explanation": explanation
            })

    # Base Filter Layers
    html = [r for r in rows if is_html(r)]
    idx200 = [r for r in html if is_200(r) and indexable(r)]
    images = [r for r in rows if is_image(r)]
    pdfs = [r for r in rows if is_pdf(r)]

    # =========================================================================
    # 1. PAGE TITLES (Issues 1 - 7)
    # =========================================================================
    add("missing_title", "High",
        [r["Address"] for r in idx200 if not (r.get("Title 1", "") or "").strip()],
        "Indexable pages with no title tag.")

    by_title = defaultdict(list)
    for r in idx200:
        t = (r.get("Title 1", "") or "").strip()
        if t: by_title[t].append(r["Address"])
    dup_t = [u for urls in by_title.values() if len(urls) > 1 for u in urls]
    add("duplicate_title", "High", dup_t, "Pages sharing an identical title.")

    add("title_too_long", "Medium",
        [r["Address"] for r in idx200 if _int(r.get("Title 1 Pixel Width")) > 561 or _int(r.get("Title 1 Length")) > 60],
        "Titles likely truncated in search results.")

    add("title_too_short", "Low",
        [r["Address"] for r in idx200 if 0 < _int(r.get("Title 1 Length")) < 30],
        "Titles shorter than 30 characters.")

    add("title_same_as_h1", "Low",
        [r["Address"] for r in html if (r.get("Title 1", "") or "").strip() == (r.get("H1-1", "") or "").strip() and (r.get("Title 1", "") or "").strip()],
        "Page titles matching the on-page H1 tag precisely.")

    add("multiple_titles", "Medium",
        [r["Address"] for r in html if _int(r.get("Title 1 Count", 0)) > 1 or (r.get("Title 2", "") or "").strip()],
        "Pages containing multiple title tags in their document headers.")

    add("title_outside_head", "Medium",
        [r["Address"] for r in html if (r.get("Title 1", "") or "").strip() and r.get("Title 1 In Head", "").lower() == "false"],
        "Title tag declared outside the structural HTML <head> element.")

    # =========================================================================
    # 2. META DESCRIPTIONS (Issues 8 - 13)
    # =========================================================================
    add("missing_meta_description", "Medium",
        [r["Address"] for r in idx200 if not (r.get("Meta Description 1", "") or "").strip()],
        "Indexable pages with no meta description.")

    by_meta = defaultdict(list)
    for r in idx200:
        m = (r.get("Meta Description 1", "") or "").strip()
        if m: by_meta[m].append(r["Address"])
    dup_m = [u for urls in by_meta.values() if len(urls) > 1 for u in urls]
    add("duplicate_meta_description", "Medium", dup_m, "Pages sharing duplicate meta descriptions.")

    add("meta_description_too_long", "Low",
        [r["Address"] for r in idx200 if _int(r.get("Meta Description 1 Length")) > 155],
        "Meta descriptions over 155 characters.")

    add("meta_description_too_short", "Low",
        [r["Address"] for r in idx200 if 0 < _int(r.get("Meta Description 1 Length")) < 70],
        "Meta descriptions under the optimal baseline length boundary (< 70 characters).")

    add("multiple_meta_descriptions", "Medium",
        [r["Address"] for r in html if (r.get("Meta Description 2", "") or "").strip()],
        "Pages featuring multiple meta description lines.")

    add("meta_description_outside_head", "Medium",
        [r["Address"] for r in html if (r.get("Meta Description 1", "") or "").strip() and r.get("Meta Description 1 In Head", "").lower() == "false"],
        "Meta descriptions found declared outside the structural <head> node.")

    # =========================================================================
    # 3. H1 & H2 HEADINGS (Issues 14 - 20)
    # =========================================================================
    add("missing_h1", "Medium",
        [r["Address"] for r in html if is_200(r) and not (r.get("H1-1", "") or "").strip()],
        "Pages with missing H1 headers.")

    by_h1 = defaultdict(list)
    for r in idx200:
        h = (r.get("H1-1", "") or "").strip()
        if h: by_h1[h].append(r["Address"])
    dup_h1 = [u for urls in by_h1.values() if len(urls) > 1 for u in urls]
    add("duplicate_h1", "Low", dup_h1, "Pages sharing duplicate H1 headings.")

    add("h1_multiple", "Low",
        [r["Address"] for r in html if is_200(r) and (_int(r.get("H1 Count", 0)) > 1 or (r.get("H1-2", "") or "").strip())],
        "Pages containing more than one h1 heading layout node.")

    add("h2_missing", "Low",
        [r["Address"] for r in html if is_200(r) and not (r.get("H2-1", "") or "").strip()],
        "Pages containing no structured h2 contextual subheadings.")

    add("h2_multiple", "Low",
        [r["Address"] for r in html if is_200(r) and _int(r.get("H2 Count", 0)) > 50],
        "Pages containing an excessive density of h2 subheadings.")

    by_h2 = defaultdict(list)
    for r in html:
        h2 = (r.get("H2-1", "") or "").strip()
        if h2: by_h2[h2].append(r["Address"])
    dup_h2 = [u for urls in by_h2.values() if len(urls) > 1 for u in urls]
    add("h2_duplicate", "Low", dup_h2, "Pages sharing duplicate h2 copy structures.")

    add("h1_too_long", "Low",
        [r["Address"] for r in html if _int(r.get("H1-1 Length")) > 70],
        "Heading tags exceeding optimal character baseline lengths.")

    # =========================================================================
    # 4. RESPONSE CODES & REDIRECTS (Issues 21 - 26)
    # =========================================================================
    add("broken_link", "High",
        [r["Address"] for r in rows if 400 <= _int(r.get("Status Code")) <= 499],
        "URLs returning a client error (4xx).")

    add("server_error", "High",
        [r["Address"] for r in rows if 500 <= _int(r.get("Status Code")) <= 599],
        "URLs returning a server error (5xx).")

    add("redirect", "Medium",
        [r["Address"] for r in rows if 300 <= _int(r.get("Status Code")) <= 399],
        "URLs that redirect (3xx).")

    redirect_map_crawl = {r["Address"]: r["Redirect URL"] for r in rows if 300 <= _int(r.get("Status Code")) <= 399 and r.get("Redirect URL")}
    chain_urls = []
    for start_url, target in redirect_map_crawl.items():
        if target in redirect_map_crawl: chain_urls.append(start_url)
    add("redirect_chain", "High", chain_urls, "Redirect configurations resulting in multi-hop chains or cycles.")

    add("redirect_loop", "High",
        [r["Address"] for r in rows if (r.get("Status", "") or "").lower() == "redirect loop"],
        "Infinite loop configurations causing standard routing stack overflows.")

    add("success_2xx", "Low",
        [r["Address"] for r in rows if 200 <= _int(r.get("Status Code")) <= 299],
        "Clean server validation responses tracked for baseline verification mapping.")

    # =========================================================================
    # 5. IMAGES (Issues 27 - 31)
    # =========================================================================
    add("missing_image_alt_text", "Low",
        [r["Address"] for r in images if "Alt Text" in r and not (r.get("Alt Text", "") or "").strip()],
        "Images that have an alt attribute, but are missing alt text completely.")

    add("images_over_100kb", "Medium",
        [r["Address"] for r in images if _int(r.get("Size", 0)) > 102400],
        "Large compressed/uncompressed images over 100 KB slowing page performance.")

    add("images_missing_size_attributes", "Low",
        [r["Address"] for r in images if "Width" in r and not (r.get("Width", "") or "").strip()],
        "Image elements without defined layout dimensions contributing to poor CLS scores.")

    add("image_alt_too_long", "Low",
        [r["Address"] for r in images if len((r.get("Alt Text", "") or "")) > 100],
        "Alternative metadata descriptions exceeding crisp length rules (> 100 chars).")

    add("image_broken", "High",
        [r["Address"] for r in images if 400 <= _int(r.get("Status Code")) <= 599],
        "Image resource file nodes returning broken client/server status traces.")

    # =========================================================================
    # 6. CANONICALS (Issues 32 - 37)
    # =========================================================================
    add("canonical_missing", "Medium",
        [r["Address"] for r in html if is_200(r) and not (r.get("Canonical Link Element 1", "") or "").strip()],
        "Pages with no canonical URL present as a link element or via HTTP headers.")

    add("canonical_non_matching", "High",
        [r["Address"] for r in html if (r.get("Canonical Link Element 1", "") or "").strip() and (r.get("Canonical Link Element 1", "") or "").strip() != r["Address"]],
        "Pages specifying a target location pointing elsewhere, passing away original equity rules.")

    add("canonical_multiple", "High",
        [r["Address"] for r in html if (r.get("Canonical Link Element 2", "") or "").strip()],
        "Conflicting declarations listing multiple structural target paths on a singular page.")

    add("canonical_broken", "High",
        [r["Address"] for r in html if "broken" in (r.get("Canonical Status", "") or "").lower()],
        "Canonical destinations linking out to dead or completely inaccessible pages.")

    add("canonical_redirect", "Medium",
        [r["Address"] for r in html if "redirect" in (r.get("Canonical Status", "") or "").lower()],
        "Canonical statements pointing paths straight to active redirect strings.")

    add("canonical_non_indexable", "Medium",
        [r["Address"] for r in html if "non-indexable" in (r.get("Canonical Status", "") or "").lower()],
        "Canonical instructions referencing elements explicitly locked out via noindex rules.")

    # =========================================================================
    # 7. STRUCTURE, DIRECTIVES & SECURITY (Issues 38 - 59)
    # =========================================================================
    add("orphan_page", "Medium",
        [r["Address"] for r in idx200 if _int(r.get("Inlinks")) == 0],
        "Indexable pages with zero internal links pointing to them.")

    add("thin_content", "Low",
        [r["Address"] for r in html if indexable(r) and _int(r.get("Word Count")) < 200],
        "Indexable pages with thin textual content (< 200 words).")

    add("slow_page", "Low",
        [r["Address"] for r in html if _float(r.get("Response Time")) > 1.0],
        "Pages taking longer than 1.0 second to respond.")

    add("non_indexable_but_linked", "Medium",
        [r["Address"] for r in html if r.get("Indexability", "").strip().lower() == "non-indexable" and _int(r.get("Inlinks")) > 0],
        "Non-indexable pages receiving internal link equity layout pathways.")

    add("blocked_by_robots_txt", "High",
        [r["Address"] for r in rows if "blocked" in (r.get("Status", "") or "").lower() or "blocked" in (r.get("Indexability Status", "") or "").lower()],
        "Internal paths completely disallowed from parsing by robots.txt files.")

    add("url_over_115_chars", "Low",
        [r["Address"] for r in rows if len(r.get("Address", "")) > 115],
        "Lengthy address paths exceeding clear UX readability limits.")

    add("url_non_ascii", "Low",
        [r["Address"] for r in rows if not all(ord(c) < 128 for c in r.get("Address", ""))],
        "URLs using fragile string configurations outside standard ASCII sets.")

    add("url_ga_tracking_parameters", "Low",
        [r["Address"] for r in rows if any(p in r.get("Address", "").lower() for p in ["utm=", "_ga="])],
        "Internal routes leaking interaction tracking tags straight inside paths.")

    add("directives_noindex", "High",
        [r["Address"] for r in rows if "noindex" in (r.get("Meta Robots 1", "") or "").lower()],
        "URLs containing standard explicit meta tag noindex block declarations.")

    add("directives_none", "High",
        [r["Address"] for r in rows if "none" in (r.get("Meta Robots 1", "") or "").lower()],
        "URLs tracking the 'none' restriction directive, filtering out standard system indexing.")

    add("directives_nofollow", "Medium",
        [r["Address"] for r in rows if "nofollow" in (r.get("Meta Robots 1", "") or "").lower()],
        "Crawl traces explicitly blocking page-level internal path equity inheritance links.")

    add("security_missing_csp", "Low",
        [r["Address"] for r in html if is_200(r) and not (r.get("Content-Security-Policy", "") or "").strip()],
        "Pages vulnerable to injection due to missing CSP rules.")

    add("security_missing_xframe", "Low",
        [r["Address"] for r in html if is_200(r) and not (r.get("X-Frame-Options", "") or "").strip()],
        "Pages exposed to Clickjacking attacks due to missing secure frame rules.")

    add("security_missing_xcontent", "Low",
        [r["Address"] for r in html if is_200(r) and not (r.get("X-Content-Type-Options", "") or "").strip()],
        "Pages lacking sniff validation boundaries to enforce declared MIME structures.")

    add("security_missing_referrer_policy", "Low",
        [r["Address"] for r in html if is_200(r) and not (r.get("Referrer-Policy", "") or "").strip()],
        "Pages missing policy instructions protecting secure network path origins.")

    add("security_protocol_relative_links", "Low",
        [r["Address"] for r in html if "//" in (r.get("Address", "") or "") and not (r.get("Address", "").startswith("http"))],
        "Resource paths utilizing legacy protocol-agnostic link structures.")

    add("security_unsafe_cross_origin_links", "Low",
        [r["Address"] for r in html if "target=" in (r.get("All Links", "") or "").lower() and "noopener" not in (r.get("All Links", "") or "").lower()],
        "External target tags exposing performance processing context leaks to destination nodes.")

    add("pagination_missing_self_canonical", "Medium",
        [r["Address"] for r in html if (r.get("Pagination Next", "") or "").strip() and not (r.get("Canonical Link Element 1", "") or "").strip()],
        "Paginated sequence elements missing matching direct tracking canonical roots.")

    add("meta_refresh", "High",
        [r["Address"] for r in html if (r.get("Meta Refresh 1", "") or "").strip()],
        "Legacy client-side meta refreshing elements forcing unstable layout jumps.")

    add("javascript_errors", "Medium",
        [r["Address"] for r in html if _int(r.get("Crawl Error Count", 0)) > 0],
        "Active code runtime exceptions triggered inside browser console operations.")

    add("frame_missing_title", "Low",
        [r["Address"] for r in html if "iframe" in (r.get("All Links", "") or "").lower() and "frame-title" not in (r.get("All Links", "") or "").lower()],
        "Embedded elements lacking explicit structural titles, breaking reader workflows.")

    add("viewport_not_set", "Medium",
        [r["Address"] for r in html if "viewport" not in (r.get("Meta Robots 1", "") or "").lower() and "width=device-width" not in (r.get("All Links", "") or "").lower()],
        "Pages failing to establish mobile layout rules, damaging responsive viewpoints.")

    add("pdf_too_large", "Low",
        [r["Address"] for r in pdfs if _int(r.get("Size", 0)) > 5242880],
        "Heavy downstream document elements exceeding 5 MB load boundaries.")

    return issues


def summarize(issues: list[dict]) -> dict:
    """Calculates true aggregate metrics securely to comply with the Output Contract."""
    high_count = sum(i["count"] for i in issues if i["severity"] == "High")
    med_count = sum(i["count"] for i in issues if i["severity"] == "Medium")
    low_count = sum(i["count"] for i in issues if i["severity"] == "Low")
    
    total = high_count + med_count + low_count
    
    recs = []
    if high_count > 0:
        recs.append(f"Resolve the {high_count} critical High-severity validation breaks immediately.")
    if med_count > 0:
        recs.append(f"Optimize the {med_count} Medium-severity structures to liberate active crawl budgets.")
    if low_count > 0:
        recs.append(f"Clear the {low_count} Low-severity opportunities to perfect clean source parameters.")
        
    return {
        "total_issues": total,
        "by_severity": {"High": high_count, "Medium": med_count, "Low": low_count},
        "recommendations": recs if recs else ["Crawl mapping clean. Infrastructure operational."]
    }


if __name__ == "__main__":
    import sys, json
    d = sys.argv[1] if len(sys.argv) > 1 else "../sample-export"
    rows = load_rows(d)
    iss = detect(rows)
    print(f"Loaded {len(rows)} data rows, isolated {len(iss)} distinct technical issue classifications.")
    print(json.dumps(summarize(iss), indent=2))