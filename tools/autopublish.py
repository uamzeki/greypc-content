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
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = "https://greypc.net/post-sitemap.xml"
TARGET_QUEUE = 7
MAX_PER_RUN = 6
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


def live_dates():
    """Dates already published on the site.

    The sitemap carries the uploaded header image for each post, and WordPress
    keeps our YYYY-MM-DD prefix even when it truncates the rest of the filename,
    so the date prefix is the only reliable join key.
    """
    req = urllib.request.Request(SITEMAP, headers={"User-Agent": "greypc-autopublish"})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read().decode("utf-8", "replace")
    return set(re.findall(r"/(\d{4}-\d{2}-\d{2})-[^/\"<]*\.(?:png|webp|jpg|jpeg)", xml))


def measure_queue(manifest):
    """Returns (unpublished_count, sitemap_ok)."""
    try:
        live = live_dates()
    except Exception as e:  # noqa: BLE001
        log(f"WARNING: could not read the sitemap ({e}). Falling back to a "
            f"single top-up article this run.")
        return TARGET_QUEUE - 1, False
    queued = [a for a in manifest["articles"] if a["publish_date"] not in live]
    return len(queued), True


# --------------------------------------------------------------------------
# validation - mirrors METHODOLOGY.md section 3 and the publishing checklist
# --------------------------------------------------------------------------

def validate(art, used_keywords):
    e = []
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
        if u not in APPROVED_LINKS:
            e.append(f"link not on the approved list: {u}")
    if not any("contact-us" in u for u in urls):
        e.append("must close with a call to action linking to /contact-us/")

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

def generate(client, methodology, entry, article_id, used_keywords, feedback=None):
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
          "- between 5 and 8 internal links, every one taken verbatim from this "
          "list, with descriptive anchor text:\n" + approved + "\n"
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
        raise RuntimeError(
            f"claude CLI exited {proc.returncode} | "
            f"stderr={proc.stderr.strip()[:600]!r} | "
            f"stdout={proc.stdout.strip()[:600]!r}"
        )
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
        write_summary(depth, depth, [], calendar)
        return 0

    used = {e["focus_keyword"] for e in calendar["calendar"]}
    pending = [e for e in calendar["calendar"] if e["status"] == "pending"]
    pending.sort(key=lambda e: e["date"])

    written, failures = [], []
    for entry in pending:
        if len(written) >= need:
            break
        article_id = f"{entry['date']}-{slugify(entry['title'])}"[:120]
        if (ROOT / "articles" / f"{article_id}.json").exists():
            log(f"SKIP {entry['date']}: article file already exists.")
            continue

        art, errors = None, None
        for attempt in (1, 2):
            try:
                candidate = generate(
                    client, methodology, entry, article_id,
                    used - {entry["focus_keyword"]},
                    feedback=errors,
                )
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
            errors = validate(candidate, used - {entry["focus_keyword"]})
            if not errors:
                art = candidate
                break
            log(f"attempt {attempt} for {article_id} failed validation: {errors}")

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

    write_summary(depth, depth + len(written), written, calendar)

    if failures:
        log(f"FAILURE: {len(failures)} article(s) could not be written to spec.")
        return 1
    if not sitemap_ok:
        log("FAILURE: the sitemap could not be read, so queue depth is a guess. "
            "Check that https://greypc.net/post-sitemap.xml still resolves.")
        return 1
    return 0


def write_summary(before, after, written, calendar):
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
        lines.append("No articles needed this run.\n")
    lines.append("### Log\n")
    lines.extend(f"- {n}" for n in notes)
    Path(os.environ.get("SUMMARY_FILE", ROOT / "run-summary.md")).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    sys.exit(main())
