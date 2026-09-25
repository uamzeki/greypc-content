#!/usr/bin/env python3
"""Grey PC autonomous content run.

Keeps the manifest queue stocked. Reads calendar.json, writes articles to the
METHODOLOGY.md spec via the Claude Code CLI, generates branded headers, and
updates manifest.json + calendar.json.

Writes files only. Committing is the workflow's job.

Exit codes:
  0  success (may have written nothing - that is valid)
  1  hard failure, workflow should open an issue
"""
import json
import os
import re
import subprocess
import sys
import html as htmlmod
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = "https://greypc.net/post-sitemap.xml"
TARGET_QUEUE = 7
MAX_PER_RUN = 6
MAX_INTERNAL_LINKS = 8
# Days of content left before the site has nothing to publish: articles queued
# but not yet live, plus calendar entries not yet written. From 2026-09-02 to
# 09-25 the site published nothing while every run reported success, because
# an empty calendar looked like "nothing to do". Below this, the run fails and
# the workflow opens an issue.
RUNWAY_ALERT_DAYS = 3
MODEL = os.environ.get("CONTENT_MODEL", "claude-sonnet-5")

APPROVED_LINKS = [
    "https://greypc.net/product-category/custom-pcs/gaming-pcs/",
    "https://greypc.net/product-category/custom-pcs/workstations/",
    "https://greypc.net/product-category/custom-pcs/laptops/",
    "https://greypc.net/product-category/custom-pcs/enterprise/",
    "https://greypc.net/product-category/pc-parts/cpu/",
    "https://greypc.net/product-category/pc-parts/graphic-cards/",
    "https://greypc.net/product-category/pc-parts/motherboard/",
    "https://greypc.net/product-category/pc-parts/ram/",
    "https://greypc.net/product-category/pc-parts/storage/",
    "https://greypc.net/product-category/pc-parts/psu/",
    "https://greypc.net/product-category/pc-parts/case/",
    "https://greypc.net/product-category/pc-parts/fans/",
    "https://greypc.net/product-category/pc-parts/aio-coolers/",
    "https://greypc.net/product-category/accesories/",
    "https://greypc.net/index.php/product-category/monitor/",
    "https://greypc.net/contact-us/",
    "https://greypc.net/about-us/",
]

# Signs that the CLI cannot produce anything at all right now. Retrying the
# next calendar entry after one of these is pointless - it will fail the same
# way, 900 seconds at a time.
FATAL_SIGNS = (
    "session limit",
    "usage limit",
    "rate limit",
    "quota",
    "unauthorized",
    "authentication",
    "invalid api key",
    "oauth token",
)


class Fatal(RuntimeError):
    """Generation is blocked for the whole run, not just this article."""


notes = []


def log(msg):
    print(msg, flush=True)
    notes.append(msg)


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write_json(name, data):
    (ROOT / name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def slugify(title):
    s = title.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


# --------------------------------------------------------------------------
# queue measurement
# --------------------------------------------------------------------------

def dedupe_manifest(manifest):
    """Drop repeat ids, keeping first occurrence. Self-heals duplicate entries
    (a duplicate silently burns a publish day, since the site walks the list)."""
    seen, out, dropped = set(), [], []
    for a in manifest["articles"]:
        if a["id"] in seen:
            dropped.append(a["id"])
            continue
        seen.add(a["id"])
        out.append(a)
    if dropped:
        manifest["articles"] = out
        log(f"Removed {len(dropped)} duplicate manifest entr(y/ies): {', '.join(dropped)}")
    return manifest


def fetch_sitemap():
    """Fetch the sitemap, retrying briefly.

    The runner intermittently cannot reach greypc.net on the first attempt
    (seen in the wild as 'Errno 101 Network is unreachable').
    """
    last = None
    for attempt in (1, 2, 3):
        try:
            req = urllib.request.Request(
                SITEMAP, headers={"User-Agent": "greypc-autopublish"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as ex:  # noqa: BLE001
            last = ex
            if attempt < 3:
                time.sleep(5 * attempt)
    raise last


# --------------------------------------------------------------------------
# live store prices
# --------------------------------------------------------------------------
# Price and buy-intent pages convert ~13x better than anything else on the
# blog (INSTRUCTIONS.md section 0), and a buyer searching "X price in Bahrain"
# wants a number. The Store API needs a login, so this reads the public
# product search page, which the runner can already reach.

PRICE_STOP = {
    "price", "prices", "in", "bahrain", "best", "2026", "for", "the", "and",
    "buying", "guide", "how", "to", "a", "of", "which", "is", "what", "build",
    "builds", "setup", "cost", "bhd", "gulf", "gcc", "buy", "cheap",
}
MAX_PRICES = 8


def price_queries(focus_keyword):
    """Store searches for a focus keyword: [(query, max_price_or_None)]."""
    kw = focus_keyword.lower()
    budget = re.search(r"under (\d+) bhd", kw)
    if budget:
        return [("gaming pc", float(budget.group(1)))]
    out = []
    for part in re.split(r"\s+vs\.?\s+", kw):
        toks = [t for t in re.findall(r"[a-z0-9]+", part) if t not in PRICE_STOP]
        if toks:
            out.append((" ".join(toks), None))
    return out


def _num(fragment):
    # Unescape first: the BHD symbol is served as hex entities (&#x62f;...),
    # whose digits would otherwise be read as the price.
    text = htmlmod.unescape(re.sub(r"<[^>]+>", " ", fragment)).replace("\xa0", " ")
    text = re.sub(r"[^\d.,\s]", " ", text)
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)", text)
    return float(m.group(1).replace(",", "")) if m else None


def search_store(query):
    """Products from greypc.net's public search page: dicts with name, price,
    url, in_stock. Returns [] on any failure - prices are a bonus, never a
    reason to fail the run."""
    url = "https://greypc.net/?" + urllib.parse.urlencode(
        {"s": query, "post_type": "product"}
    )
    page = None
    for attempt in (1, 2, 3):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "greypc-autopublish"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                page = r.read().decode("utf-8", "replace")
            break
        except Exception as ex:  # noqa: BLE001 - the host rate-limits bursts
            if attempt == 3:
                log(f"price lookup failed for '{query}': {ex}")
                return []
            time.sleep(4 * attempt)
    items = []
    for block in re.split(r"<li\b", page)[1:]:
        head = block[:600]
        if "type-product" not in head:
            continue
        block = block.split("</li>")[0]
        link = re.search(r'href="(https://greypc\.net/product/[^"#?]+)"', block)
        name = re.search(
            r'woocommerce-loop-product__title[^>]*>(.*?)</', block, re.S
        ) or re.search(r'<h[23][^>]*>(.*?)</h[23]>', block, re.S)
        price_html = re.search(r'class="price"[^>]*>(.*?)</span>\s*(?:</a>|<a|</div>|$)', block, re.S)
        price_html = price_html.group(1) if price_html else block
        sale = re.search(r"<ins[^>]*>(.*?)</ins>", price_html, re.S)
        amounts = re.findall(r"<bdi>(.*?)</bdi>", sale.group(1) if sale else price_html, re.S)
        price = _num(amounts[0]) if amounts else None
        if not (link and name and price):
            continue
        items.append({
            "name": htmlmod.unescape(re.sub(r"<[^>]+>", "", name.group(1))).strip(),
            "price": price,
            "url": link.group(1) if link.group(1).endswith("/") else link.group(1) + "/",
            "in_stock": "outofstock" not in head,
        })
    return items


BUY_INTENT = re.compile(r"\b(price|bhd|best|vs|build|buy|cost|under|cheap|deal)\b")
GENERIC = {"gaming", "pc", "pcs", "computer", "desktop"}


def live_prices(focus_keyword):
    """Relevant in-stock products first, deduplicated, capped at MAX_PRICES.
    Only for buying-intent keywords - a how-to does not need a price list."""
    if not BUY_INTENT.search(focus_keyword.lower()):
        return []
    seen, found = set(), []
    for i, (query, cap) in enumerate(price_queries(focus_keyword)):
        if i:
            time.sleep(2)
        need = [t for t in query.split() if len(t) >= 3 and t not in GENERIC]
        for it in search_store(query):
            name = re.sub(r"[\s-]", "", it["name"].lower())
            if need and not any(t.replace("-", "") in name for t in need):
                continue
            if cap and not re.search(r"\bpc\b|build", it["name"].lower()):
                continue  # a budget-build article wants whole PCs, not parts
            if it["url"] in seen or (cap and it["price"] > cap):
                continue
            seen.add(it["url"])
            found.append(it)
    found.sort(key=lambda it: (not it["in_stock"], it["price"]))
    return found[:MAX_PRICES]


def live_keys():
    """Two independent 'this article is already live' signals, unioned.

    * the post slug from <loc> - present for every post, always
    * the YYYY-MM-DD prefix of the header image, which WordPress keeps even
      when it truncates the rest of the filename

    The image signal alone has a blind spot: the sitemap is regenerated as soon
    as a post goes live, but the header image can take a while to attach, so a
    freshly published post can appear with no <image:loc> at all. Counting that
    post as still-queued inflates the measured depth and quietly starves the
    queue. The slug is always there, so the union is reliable.
    """
    xml = fetch_sitemap()
    slugs = set(re.findall(r"greypc\.net/([a-z0-9][a-z0-9-]*)/", xml))
    dates = set(re.findall(r"/(\d{4}-\d{2}-\d{2})-[^/\"<]*\.(?:png|webp|jpg|jpeg)", xml))
    return slugs, dates


def measure_queue(manifest):
    """Returns (unpublished_count, sitemap_ok)."""
    try:
        slugs, dates = live_keys()
    except Exception as e:  # noqa: BLE001
        log(f"WARNING: could not read the sitemap after 3 tries ({e}). Topping "
            f"up by a single article and leaving the real check for tomorrow.")
        return TARGET_QUEUE - 1, False
    queued = []
    for a in manifest["articles"]:
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", a["id"])
        if slug in slugs or a["publish_date"] in dates:
            continue
        queued.append(a)
    return len(queued), True


# --------------------------------------------------------------------------
# internal-link repair
# --------------------------------------------------------------------------

LINK_RE = re.compile(
    r'<a\b[^>]*\bhref="(https://greypc\.net[^"]*)"[^>]*>(.*?)</a>', re.I | re.S
)


def cap_internal_links(html, limit=MAX_INTERNAL_LINKS):
    """Unwrap repeated and surplus internal links, keeping their anchor text.

    Drafts kept landing on 9-10 links (issues #3-#16), usually by linking the
    same category twice or adding links inside FAQ answers, and every miss
    burned a full retry. Unwrapping leaves each sentence intact, so this is a
    repair, not a relaxation: validate() still enforces 5-8.

    Keeps the first link to each URL and the last /contact-us/ link (the
    closing call to action), then trims from the end of the article down to
    the limit. Returns (html, number_of_links_removed).
    """
    matches = list(LINK_RE.finditer(html))
    if len(matches) <= 1:
        return html, 0
    contact = [i for i, m in enumerate(matches) if "contact-us" in m.group(1)]
    cta = contact[-1] if contact else None
    keep, seen = [], set()
    for i, m in enumerate(matches):
        url = m.group(1)
        if "contact-us" in url or url in seen:
            continue
        seen.add(url)
        keep.append(i)
    keep = keep[: limit - (1 if cta is not None else 0)]
    if cta is not None:
        keep.append(cta)
    keep = set(keep)
    removed = len(matches) - len(keep)
    if not removed:
        return html, 0
    out, pos = [], 0
    for i, m in enumerate(matches):
        out.append(html[pos:m.start()])
        out.append(m.group(0) if i in keep else m.group(2))
        pos = m.end()
    out.append(html[pos:])
    return "".join(out), removed


# --------------------------------------------------------------------------
# validation - mirrors METHODOLOGY.md section 3 and the publishing checklist
# --------------------------------------------------------------------------

def validate(art, used_keywords, prices=()):
    e = []
    product_urls = {p["url"] for p in prices}
    kw = art.get("focus_keyword", "").lower()
    html = art.get("content_html", "")

    if len(art.get("seo_title", "")) > 60:
        e.append(f"seo_title is {len(art.get('seo_title',''))} chars, max 60")
    if "grey pc" not in art.get("seo_title", "").lower():
        e.append("seo_title must contain 'Grey PC'")

    md = art.get("meta_description", "")
    if not 140 <= len(md) <= 160:
        e.append(f"meta_description is {len(md)} chars, must be 140-160")
    if kw not in md.lower():
        e.append("meta_description must contain the exact focus keyword")

    if kw not in html.lower():
        e.append("content_html must contain the exact focus keyword")
    if kw in {k.lower() for k in used_keywords}:
        e.append(f"focus keyword '{kw}' has already been used")

    words = len(re.sub(r"<[^>]+>", " ", html).split())
    if not 1300 <= words <= 1800:
        e.append(f"word count is {words}, must be 1300-1800")

    urls = re.findall(r'href="(https://greypc\.net[^"]*)"', html)
    if not 5 <= len(urls) <= 8:
        e.append(f"{len(urls)} internal links, must be 5-8")
    for u in urls:
        if u not in APPROVED_LINKS and u not in product_urls:
            e.append(f"link not on the approved list: {u}")
    if not any("contact-us" in u for u in urls):
        e.append("must close with a call to action linking to /contact-us/")

    # Every BHD figure must be a live price or a budget named in the title.
    allowed = {round(p["price"], 2) for p in prices}
    for n in re.findall(r"\d[\d,]*(?:\.\d+)?", art.get("title", "") + " " + kw):
        allowed.add(round(float(n.replace(",", "")), 2))
    text = re.sub(r"<[^>]+>", " ", html)
    for a, b in re.findall(
        r"(?:BHD|BD|\.د\.ب)\s*(\d[\d,]*(?:\.\d+)?)|(\d[\d,]*(?:\.\d+)?)\s*(?:BHD|BD)\b",
        text,
    ):
        val = round(float((a or b).replace(",", "")), 2)
        if val not in allowed:
            e.append(f"price {a or b} BHD is not a live Grey PC price - quote only "
                     f"the prices supplied, or describe the tier without a number")
            break

    if re.search(r"<h1", html, re.I):
        e.append("content_html must never contain an H1")
    if "<h2>Frequently Asked Questions</h2>" not in html:
        e.append("missing the required 'Frequently Asked Questions' H2 block")
    if len(re.findall(r"<h3", html, re.I)) < 4:
        e.append("FAQ must have at least 4 H3 questions")

    for field in ("id", "title", "slug", "excerpt", "featured_image_alt", "tags"):
        if not art.get(field):
            e.append(f"missing required field: {field}")
    if len(art.get("tags", [])) < 5:
        e.append("need 5-6 tags")
    return e


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------

def generate(client, methodology, entry, article_id, used_keywords,
             feedback=None, prices=()):
    approved = "\n".join(APPROVED_LINKS)
    system = (
        methodology
        + "\n\n---\n\nYou are writing one article for Grey PC, a computer shop in "
          "Bahrain. Follow the methodology above exactly. Reply with a single JSON "
          "object and nothing else - no prose, no code fences.\n\n"
          "Required keys: id, title, slug, seo_title, meta_description, "
          "focus_keyword, category, tags, excerpt, featured_image_alt, content_html.\n\n"
          "Hard requirements, all of which are checked automatically:\n"
          "- seo_title: 60 chars max, must contain 'Grey PC'\n"
          "- meta_description: between 140 and 160 characters, must contain the "
          "exact focus keyword\n"
          "- content_html: 1300-1800 words, starts at H2, never an H1\n"
          "- the exact focus keyword appears in the first paragraph inside <strong> "
          "tags, in at least one H2, and in the closing section\n"
          "- a 'Frequently Asked Questions' H2 with 4-6 H3 questions, each answered "
          "in 40-60 words\n"
          "- a 'The Bottom Line' summary section near the end\n"
          "- exactly 6 internal links. The checker rejects fewer than 5 or more "
          "than 8, and drafts keep failing at 9-10. Link each URL once only, "
          "put no links inside the FAQ answers, and count your <a> tags before "
          "you reply. The contact-us call to action is one of the 6. Every URL "
          "must come verbatim from this list, with descriptive anchor text:\n"
          + approved + "\n"
          "- close with a call to action linking to https://greypc.net/contact-us/\n"
          "- HTML entities (&ndash; &rsquo; &mdash;) rather than raw unicode "
          "punctuation\n"
          "- no invented prices, benchmark figures or product SKUs\n\n"
          "If the topic has genuinely gone stale - a dated seasonal hook that has "
          "passed, or hardware that has been superseded - reply instead with "
          '{"stale": true, "reason": "..."} and nothing else.'
    )
    user = (
        f"Write today's article.\n\n"
        f"id: {article_id}\n"
        f"title: {entry['title']}  (this title is final - do not rewrite it)\n"
        f"focus_keyword: {entry['focus_keyword']}\n"
        f"category: {entry.get('category', 'Blog')}\n"
        f"slug: {slugify(entry['title'])}\n"
        f"today's date: {os.environ.get('RUN_DATE', 'unknown')}\n\n"
        f"Focus keywords already used elsewhere on the site, do not reuse any of "
        f"them: {', '.join(sorted(used_keywords))}"
    )
    if prices:
        run_date = os.environ.get("RUN_DATE", "today")
        user += (
            f"\n\nLIVE GREY PC PRICES, checked {run_date}. These are the only prices "
            f"you may state. Quote them exactly in BHD, name the product, and link "
            f"its product page (product links count toward the 6 internal links; "
            f"link 2-3 of them). Say once that prices were checked on {run_date} "
            f"and can change - ask the reader to message Grey PC for today's price "
            f"and a build quote. Prefer in-stock items; call out-of-stock items "
            f"'available to order'.\n"
            + "\n".join(
                f"- {p['name']} | {p['price']:.3f} BHD | "
                f"{'in stock' if p['in_stock'] else 'out of stock'} | {p['url']}"
                for p in prices
            )
        )
    if feedback:
        user += (
            "\n\nYour previous attempt failed automated validation with these "
            "errors. Fix every one of them:\n- " + "\n- ".join(feedback)
        )

    proc = subprocess.run(
        ["claude", "-p",
         "--model", MODEL,
         "--append-system-prompt", system],
        input=user,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if proc.returncode != 0:
        msg = (
            f"claude CLI exited {proc.returncode} | "
            f"stderr={proc.stderr.strip()[:600]!r} | "
            f"stdout={proc.stdout.strip()[:600]!r}"
        )
        blob = (proc.stdout + proc.stderr).lower()
        if any(sign in blob for sign in FATAL_SIGNS):
            raise Fatal(msg)
        raise RuntimeError(msg)
    text = proc.stdout.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


def make_header(title, article_id):
    out = ROOT / "images" / f"{article_id}.png"
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "make_header.py"), title, str(out)],
        check=True, capture_output=True,
    )
    if not out.exists() or out.stat().st_size < 10_000:
        raise RuntimeError(f"header image for {article_id} looks wrong")
    return out


# --------------------------------------------------------------------------

def main():
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        log("FAILURE: CLAUDE_CODE_OAUTH_TOKEN is not set. Generate one with "
            "'claude setup-token' and add it under repository Settings > "
            "Secrets and variables > Actions.")
        return 1

    client = None  # generation shells out to the Claude Code CLI
    methodology = (ROOT / "METHODOLOGY.md").read_text(encoding="utf-8")
    # Performance-derived rules. Where they conflict with METHODOLOGY.md,
    # INSTRUCTIONS.md wins - it is built from what actually ranked.
    instructions = ROOT / "INSTRUCTIONS.md"
    if instructions.exists():
        methodology += "\n\n---\n\n" + instructions.read_text(encoding="utf-8")
    manifest = dedupe_manifest(read_json("manifest.json"))
    calendar = read_json("calendar.json")
    dirty = bool(notes)  # dedupe may already have changed the manifest

    depth, sitemap_ok = measure_queue(manifest)
    need = min(TARGET_QUEUE - depth, MAX_PER_RUN)
    log(f"Queue depth before: {depth} unpublished. Target {TARGET_QUEUE}.")

    if need <= 0:
        log("Queue is healthy - no articles needed this run.")
        if dirty:
            write_json("manifest.json", manifest)
        write_summary(depth, depth, [], calendar,
                      "Queue is full - no articles needed this run.")
        return 0

    used = {e["focus_keyword"] for e in calendar["calendar"]}
    pending = [e for e in calendar["calendar"] if e["status"] == "pending"]
    pending.sort(key=lambda e: e["date"])

    written, failures = [], []
    attempted, fatal = 0, None
    for entry in pending:
        # Bound the run by attempts, not just successes. Previously the loop
        # only stopped once `need` articles had been written, so a run where
        # generation was failing would grind through every pending entry -
        # 38 of them on 2026-08-10, two attempts each, all doomed.
        if len(written) >= need or attempted >= need:
            break
        article_id = f"{entry['date']}-{slugify(entry['title'])}"[:120]
        if (ROOT / "articles" / f"{article_id}.json").exists():
            log(f"SKIP {entry['date']}: article file already exists.")
            continue

        attempted += 1
        prices = live_prices(entry["focus_keyword"])
        log(f"{len(prices)} live price(s) for '{entry['focus_keyword']}'")
        art, errors = None, None
        for attempt in (1, 2):
            try:
                candidate = generate(
                    client, methodology, entry, article_id,
                    used - {entry["focus_keyword"]},
                    feedback=errors, prices=prices,
                )
            except Fatal as ex:
                fatal = str(ex)
                errors = [f"fatal: {ex}"]
                break
            except Exception as ex:  # noqa: BLE001
                errors = [f"generation error: {ex}"]
                continue
            if candidate.get("stale"):
                entry["status"] = "skipped"
                dirty = True
                log(f"SKIPPED {entry['date']} '{entry['title']}' as stale: "
                    f"{candidate.get('reason', 'no reason given')}")
                art = "stale"
                break
            candidate["id"] = article_id
            candidate["category"] = entry.get("category", "Blog")
            candidate["focus_keyword"] = entry["focus_keyword"]
            candidate["title"] = entry["title"]
            candidate["featured_image_url"] = (
                "https://raw.githubusercontent.com/uamzeki/greypc-content/main/"
                f"images/{article_id}.png"
            )
            candidate["content_html"], trimmed = cap_internal_links(
                candidate.get("content_html", "")
            )
            if trimmed:
                log(f"trimmed {trimmed} repeated/surplus internal link(s) "
                    f"from {article_id}")
            errors = validate(candidate, used - {entry["focus_keyword"]}, prices)
            if not errors:
                art = candidate
                break
            log(f"attempt {attempt} for {article_id} failed validation: {errors}")

        if fatal:
            log(f"ABORTING the run early - generation is blocked: {fatal}")
            break
        if art == "stale":
            continue
        if art is None:
            failures.append((article_id, errors))
            log(f"FAILED {article_id} after 2 attempts: {errors}")
            continue

        write_json(f"articles/{article_id}.json", art)
        make_header(entry["title"], article_id)
        manifest["articles"].append(
            {"id": article_id, "url": f"{article_id}.json",
             "publish_date": entry["date"]}
        )
        entry["status"] = "published"
        used.add(entry["focus_keyword"])
        written.append((article_id, entry["title"], entry["focus_keyword"]))
        dirty = True
        log(f"WROTE {article_id}")

    if written or dirty:
        manifest["updated"] = os.environ.get("RUN_DATE", manifest.get("updated"))
        write_json("manifest.json", manifest)
        write_json("calendar.json", calendar)

    queued = depth + len(written)
    pending_left = sum(1 for e in calendar["calendar"] if e["status"] == "pending")
    runway = queued + pending_left
    log(f"Runway: {runway} day(s) of content ({queued} queued + "
        f"{pending_left} pending in the calendar).")
    headline = None
    if not written and not pending:
        headline = ("Nothing written - calendar.json has no pending entries. "
                    "Extend the calendar.")
    runway_low = runway < RUNWAY_ALERT_DAYS
    if runway_low:
        # Logged before write_summary so it lands in the issue body.
        log(f"FAILURE: only {runway} day(s) of content left. The site stops "
            f"publishing when this reaches 0. Extend calendar.json.")
    write_summary(depth, queued, written, calendar, headline)

    if fatal:
        log("FAILURE: generation is blocked, so the run stopped after the first "
            "article rather than burning the whole calendar. " + fatal)
        return 1
    if failures:
        log(f"FAILURE: {len(failures)} article(s) could not be written to spec.")
        return 1
    if not sitemap_ok:
        log("NOTE: queue depth was estimated this run because the sitemap was "
            "unreachable after 3 tries. Not failing the run for that alone - "
            "the daily health check flags it if it keeps happening.")
    return 1 if runway_low else 0


def write_summary(before, after, written, calendar, headline=None):
    pending = len([e for e in calendar["calendar"] if e["status"] == "pending"])
    lines = [
        "## Grey PC content run",
        "",
        f"- Queue depth: **{before} -> {after}** unpublished (target {TARGET_QUEUE})",
        f"- Calendar entries still pending: **{pending}**",
        "",
    ]
    if written:
        lines.append("### Written this run")
        lines.append("")
        lines.append("| Article | Focus keyword |")
        lines.append("|---|---|")
        for _id, title, kw in written:
            lines.append(f"| {title} | `{kw}` |")
        lines.append("")
    else:
        lines.append((headline or "No articles written this run.") + "\n")
    lines.append("### Log\n")
    lines.extend(f"- {n}" for n in notes)
    Path(os.environ.get("SUMMARY_FILE", ROOT / "run-summary.md")).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
