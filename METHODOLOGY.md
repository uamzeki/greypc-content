# Grey PC Content Methodology

**Read this file in full before writing or publishing any article.**

Repo: uamzeki/greypc-content · Site: https://greypc.net · Market: Bahrain / GCC

---

## 1. How the pipeline works

The website ingests content from this repository. Nothing is written directly into WordPress.

    calendar.json        ->  the editorial plan (titles are USER-EDITABLE)
    articles/<id>.json   ->  one JSON file per article (the actual content)
    images/<id>.png      ->  1200x675 branded header, from tools/make_header.py
    manifest.json        ->  the feed the site reads; an article is only live once listed here

The id and the filenames must match exactly: YYYY-MM-DD-slug

manifest.base_url is https://raw.githubusercontent.com/uamzeki/greypc-content/main/articles/

**An article is not published until all four are committed:** the article JSON, the image,
the manifest entry, and the calendar status flipped to published.

---

## 2. Monthly planning (runs on the 1st)

1. Read calendar.json and list every focus_keyword already used. **Never repeat a keyword.**
2. Research keywords for the coming month. Target the intersection of:
   - **Commercial intent** - "best X", "X vs Y", "X price bahrain", "X under N BHD"
   - **Local intent** - anything that can carry "Bahrain" or "Gulf" naturally
   - **Low competition** - long-tail, specific, question-shaped
   - **Product alignment** - the topic must map to a real greypc.net category
3. Append one entry per day for the whole month, in this shape:

    { "date": "2026-08-19", "title": "...", "focus_keyword": "...", "category": "Blog", "status": "pending" }

4. Keep a healthy mix across the month, roughly:
   - 35% build guides (budget tiers, use-case builds)
   - 30% comparisons (X vs Y)
   - 20% buyer's guides for a single component or peripheral
   - 15% how-to / maintenance / troubleshooting

**Titles are editable by the owner.** Never rewrite a pending title that has been changed.
If a title differs from what was originally generated, treat the owner's version as final and
derive the slug and the content angle from it.

---

## 3. Daily article writing

Take the calendar.json entry whose date is today and whose status is pending.
If today has no pending entry, take the **oldest** pending entry - clear the backlog first.

### Required fields

| Field | Rule |
|---|---|
| seo_title | 60 characters max, must contain "Grey PC" and the keyword or a close variant |
| meta_description | 140-160 characters, must contain the exact focus keyword |
| excerpt | 1-2 natural sentences containing the keyword or a variant |
| slug | lowercase, hyphenated, derived from the title |
| tags | 5-6 tags, mix of topic + local + category |
| focus_keyword | exactly as written in calendar.json |
| featured_image_alt | descriptive, includes the topic, never keyword-stuffed |
| content_html | 1,300-1,800 words |

Assertions to run before writing the file (see tools/build_today.py for the pattern):
seo_title length under 61, meta_description length between 140 and 160, keyword present in the
meta description and in content_html, "grey pc" present in seo_title.

### Content rules

- **One H1 equivalent** - the title field. The body starts at H2. Never emit an H1 in content_html.
- The exact focus keyword appears in: the first paragraph (inside strong tags), at least one H2,
  and the closing section. Density around 0.8-1.2%. **Do not stuff.**
- Use semantic variants and related entities throughout rather than repeating the exact phrase.
- Short paragraphs, 2-4 sentences. Use lists only where a list is genuinely clearer.
- **Every article must include a "Frequently Asked Questions" H2** with 4-6 H3 questions, each
  answered in 40-60 words. This is the single highest-value block for AI and answer engines.
- 5-8 internal links, in context, with descriptive anchor text. Never "click here".
- Close with a call to action linking to https://greypc.net/contact-us/
- No fabricated benchmark numbers, no invented prices, no invented product SKUs. Where a specific
  figure would be needed, describe the tier or the trade-off instead. Prices are always BHD.
- Use HTML entities (&ndash; &rsquo; &mdash;) rather than raw unicode punctuation.

### Approved internal link targets

    https://greypc.net/product-category/custom-pcs/gaming-pcs/
    https://greypc.net/product-category/custom-pcs/workstations/
    https://greypc.net/product-category/custom-pcs/laptops/
    https://greypc.net/product-category/custom-pcs/enterprise/
    https://greypc.net/product-category/pc-parts/cpu/
    https://greypc.net/product-category/pc-parts/graphic-cards/
    https://greypc.net/product-category/pc-parts/motherboard/
    https://greypc.net/product-category/pc-parts/ram/
    https://greypc.net/product-category/pc-parts/storage/
    https://greypc.net/product-category/pc-parts/psu/
    https://greypc.net/product-category/pc-parts/case/
    https://greypc.net/product-category/pc-parts/fans/
    https://greypc.net/product-category/pc-parts/aio-coolers/
    https://greypc.net/product-category/accesories/        <- note the site's spelling
    https://greypc.net/index.php/product-category/monitor/
    https://greypc.net/contact-us/
    https://greypc.net/about-us/

---

## 4. GEO / AEO - being cited by AI assistants

Traditional SEO wins the click. GEO wins the citation. Every article must:

1. **Answer the title question in the first 60 words.** No throat-clearing intro.
2. **Use self-contained, extractable paragraphs.** An assistant should be able to lift any single
   paragraph and have it make sense without the surrounding context.
3. **Include the FAQ block.** Question-shaped headings map directly onto how people prompt AI.
4. **State concrete, checkable facts** - weight ranges, wattage ranges, capacity thresholds,
   rules of thumb. Vague copy never gets cited.
5. **Add a definitive summary section** near the end ("The Bottom Line") restating the answer
   plainly in 3-5 sentences.
6. **Claim the local angle explicitly** - "in Bahrain", "in the Gulf", "45C summers", "BHD".
   This is Grey PC's defensible moat. Global sites cannot compete on it.
7. **Be genuinely useful and specific.** Both search and AI ranking reward first-hand perspective,
   direct recommendations, and honest trade-offs over hedged generic advice.

---

## 5. Tone

Knowledgeable local shop, not a content mill. Confident, practical, plain English.
Give a real recommendation. Name the trade-off. Never hype.
Never claim a product is "in stock" and never quote a specific price - link to the category page.

---

## 6. Publishing checklist

- [ ] Read this file
- [ ] Focus keyword not already used in calendar.json
- [ ] articles/<id>.json created and all assertions pass
- [ ] images/<id>.png generated via tools/make_header.py
- [ ] manifest.json - entry appended, updated field set to today
- [ ] calendar.json - that date's status flipped to published
- [ ] Word count 1,300-1,800
- [ ] FAQ section present
- [ ] 5-8 internal links, all from the approved list
- [ ] Committed and pushed to main

---

*Last updated: 2026-08-08*
