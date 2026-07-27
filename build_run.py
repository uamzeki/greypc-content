import json

ROOT = "."
ID = "2026-07-15-how-to-build-a-quiet-dust-resistant-pc-for-the-gulf"
TITLE = "How to Build a Quiet, Dust-Resistant PC for the Gulf"
SLUG = "how-to-build-a-quiet-dust-resistant-pc-for-the-gulf"
KEYWORD = "dust resistant pc build"
ENTRY_DATE = "2026-07-15"
TODAY = "2026-07-27"

seo_title = "Quiet, Dust-Resistant PC Build Guide – Grey PC"
meta_description = ("Planning a dust resistant pc build for Bahrain or the Gulf? Get case, "
                     "airflow, and cooling tips that keep your PC quiet and running cool for years.")
excerpt = ("Desert dust and Gulf heat are the two biggest threats to any gaming PC. Here is how "
           "to plan a dust resistant pc build that stays cool, quiet, and reliable for years.")

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
    "tags": ["pc cooling", "dust protection", "case airflow", "bahrain pc build", "quiet pc build", "maintenance"],
    "excerpt": excerpt,
    "featured_image_url": f"https://raw.githubusercontent.com/uamzeki/greypc-content/main/images/{ID}.png",
    "featured_image_alt": "Grey PC header graphic for a quiet, dust-resistant PC build guide",
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
