import json, io

ROOT = "/tmp/gc_work"
ID = "2026-07-14-best-gaming-headset-for-bahrain-gamers-2026"
TITLE = "Best Gaming Headset for Bahrain Gamers 2026"
SLUG = "best-gaming-headset-for-bahrain-gamers-2026"
KEYWORD = "best gaming headset bahrain"
ENTRY_DATE = "2026-07-14"

seo_title = "Best Gaming Headset for Bahrain Gamers – Grey PC"
meta_description = ("Looking for the best gaming headset bahrain gamers can trust in 2026? "
                     "Compare wired vs wireless, comfort, and budget tiers before you buy today.")
excerpt = ("Picking the best gaming headset bahrain players can rely on comes down to audio "
           "accuracy, mic clarity, and comfort built for long sessions in the heat.")

assert len(seo_title) <= 60, f"seo_title too long: {len(seo_title)}"
assert 140 <= len(meta_description) <= 160, f"meta_description len {len(meta_description)}"
assert KEYWORD in meta_description.lower()
assert "grey pc" in seo_title.lower()

with open(f"{ROOT}/tools/body.html", "r", encoding="utf-8") as f:
    content_html = f.read().strip()

article = {
    "id": ID,
    "title": TITLE,
    "slug": SLUG,
    "seo_title": seo_title,
    "meta_description": meta_description,
    "focus_keyword": KEYWORD,
    "category": "Blog",
    "tags": ["gaming headset", "bahrain gaming", "pc accessories", "wireless headset", "buyer's guide"],
    "excerpt": excerpt,
    "featured_image_url": f"https://raw.githubusercontent.com/uamzeki/greypc-content/main/images/{ID}.png",
    "featured_image_alt": "Gamer wearing a gaming headset in front of a custom PC setup in Bahrain",
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
manifest["updated"] = "2026-07-26"

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
