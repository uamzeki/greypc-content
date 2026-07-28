import json

ROOT = "/tmp/gc"
ID = "2026-07-16-rtx-5060-vs-5060-ti-best-1080p-1440p-value-in-2026"
TITLE = "RTX 5060 vs 5060 Ti: Best 1080p/1440p Value in 2026"
SLUG = "rtx-5060-vs-5060-ti-best-1080p-1440p-value-in-2026"
KEYWORD = "rtx 5060 vs 5060 ti"
ENTRY_DATE = "2026-07-16"
TODAY = "2026-07-28"

seo_title = "RTX 5060 vs 5060 Ti: Which to Buy? - Grey PC"
meta_description = ("Comparing the rtx 5060 vs 5060 ti for your next build? See the real "
                     "differences in VRAM, 1440p performance, and long-term value before buying in Bahrain.")
excerpt = ("Choosing between the RTX 5060 vs 5060 Ti comes down to your target resolution, "
           "VRAM needs, and how long you plan to keep the card.")

print("seo_title len:", len(seo_title))
print("meta_description len:", len(meta_description))

assert len(seo_title) <= 60, f"seo_title too long: {len(seo_title)}"
assert 140 <= len(meta_description) <= 160, f"meta_description len {len(meta_description)}"
assert KEYWORD in meta_description.lower(), "keyword missing from meta_description"
assert "grey pc" in seo_title.lower(), "grey pc missing from seo_title"

with open(f"{ROOT}/tools/body.html", "r", encoding="utf-8") as f:
    content_html = f.read().strip()

assert KEYWORD in content_html.lower(), "keyword missing from content_html"

article = {
    "id": ID,
    "title": TITLE,
    "slug": SLUG,
    "seo_title": seo_title,
    "meta_description": meta_description,
    "focus_keyword": KEYWORD,
    "category": "Blog",
    "tags": ["rtx 5060", "rtx 5060 ti", "gpu buying guide", "bahrain gaming", "1440p gaming", "graphics card"],
    "excerpt": excerpt,
    "featured_image_url": f"https://raw.githubusercontent.com/uamzeki/greypc-content/main/images/{ID}.png",
    "featured_image_alt": "RTX 5060 vs 5060 Ti graphics card comparison header graphic for Grey PC Bahrain",
    "content_html": content_html,
}

with open(f"{ROOT}/articles/{ID}.json", "w", encoding="utf-8") as f:
    json.dump(article, f, ensure_ascii=False, indent=2)
    f.write("\n")

# --- manifest.json ---
with open(f"{ROOT}/manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

manifest["articles"].append({
    "id": ID,
    "url": f"{ID}.json",
    "publish_date": ENTRY_DATE,
})
manifest["updated"] = TODAY

with open(f"{ROOT}/manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
    f.write("\n")

# --- calendar.json ---
with open(f"{ROOT}/calendar.json", "r", encoding="utf-8") as f:
    calendar = json.load(f)

found = False
for entry in calendar["calendar"]:
    if entry["date"] == ENTRY_DATE and entry["status"] == "pending":
        entry["status"] = "published"
        found = True
        break

assert found, "target calendar entry not found/pending"

with open(f"{ROOT}/calendar.json", "w", encoding="utf-8") as f:
    json.dump(calendar, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("OK - seo_title len:", len(seo_title), "meta_description len:", len(meta_description))
print("article word count (tag-inclusive split):", len(content_html.split()))
