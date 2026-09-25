# Grey PC - Performance Instructions

**Read this before planning topics or writing an article.** These rules come from what actually
ranked on greypc.net. Where they conflict with METHODOLOGY.md, this file wins.

Source: Google Search Console via Site Kit (wp-admin), 2026-06-20 to 2026-09-23.
Last refreshed: 2026-09-25. Refresh on the 1st of each month, before planning.

---

## 1. The top 10 articles (by Google clicks)

| # | Article | Clicks | Impressions | Avg pos | Written by |
|---|---|---:|---:|---:|---|
| 1 | NVIDIA Control Panel Best Settings: The Ultimate 2026 Performance Guide | 421 | 27,938 | 5.1 | pre-pipeline |
| 2 | RTX 5080 vs RX 9070 XT: 1440p & 4K Value in 2026 | 293 | 41,136 | 7.1 | pipeline |
| 3 | Best AIO Cooler for Ryzen 7 9800X3D in 2026 | 274 | 11,757 | 6.2 | pipeline |
| 4 | Flight Simulator 2026 PC Build: The Ultimate Guide | 199 | 7,895 | 7.0 | pre-pipeline |
| 5 | CMD Commands (Arabic) | 157 | 7,562 | 5.5 | 2024, 207 words |
| 6 | Best PC Build for Fortnite 240FPS in 2026 | 111 | 11,746 | 5.7 | pipeline |
| 7 | AIO Cooler with LCD Screen: The Ultimate 2026 Guide | 104 | 8,822 | 6.8 | pre-pipeline |
| 8 | The Ultimate Gaming PC Build 2026 | 95 | 10,931 | 6.6 | pre-pipeline |
| 9 | Ultimate Workstation for CFD and FEA Analysis | 89 | 4,125 | 6.5 | pre-pipeline |
| 10 | How to Choose a CPU for 3D Rendering | 81 | 10,175 | 6.0 | pre-pipeline |

## 2. Why these ten win

1. **Each one answers a query people actually type, and that query names something specific.**
   The top queries behind them: "nvidia control panel best settings", "9070xt vs 5080",
   "best aio for 9800x3d", "best pc for flight simulator 2026", "240 fps fortnite pc",
   "cfd workstation", "best cpu for rendering". A product, a game, or a piece of software is in
   every head query.
2. **They are decision questions** - which one, what settings, what do I need - asked by someone
   about to buy or change something.
3. **They are narrow enough that a small site can rank.** Big publishers target "best CPU cooler";
   nobody targets "best AIO for the 9800X3D" as precisely, so Grey PC sits at position 5-7.
4. **Length is not the reason.** #3 is 715 words and #5 is 207 words. The 3,000-word
   "ultimate guide" batch produced five of the top ten, but across its 79 URLs the median is
   **4 clicks** and 33 got none - the winners won on topic choice, not format.
5. **None of them targets "Bahrain".**

## 3. What the whole pipeline shows (73 articles)

| Keyword type | Articles | Clicks | Median clicks |
|---|---:|---:|---:|
| Names a product, game or software, no "Bahrain" | 35 | 1,183 | 7 |
| Generic, no "Bahrain" | 17 | 97 | 3 |
| Carries "Bahrain" or "BHD" | 21 | 86 | 1 |

- **"Bahrain" keywords have almost no search demand.** "mechanical keyboard bahrain" had 35
  impressions in three months. All 21 local articles together drew 7,597 impressions - under a
  fifth of the single "RTX 5080 vs RX 9070 XT" page.
- **They do not bring more local readers either.** In the page-by-country data, the 18 Bahrain-keyword
  pages and the 42 global-keyword pages each brought **9 clicks from Bahrain**. Global keywords
  delivered the same local reach plus 28 times the total traffic.
- **Bahrain buyers arrive through the homepage and product pages**, not the blog. In the same
  page-by-country data, 1,407 of the homepage's 1,547 clicks are from Bahrain, and articles
  supply about 3% of all Bahrain clicks.
  The blog's job is authority and reach; the local sale happens on the shop pages.
- **The one local article that works is price intent**: "DDR5 RAM price in Bahrain" - 44 clicks,
  7% CTR, every tracked click from the GCC.
- **CTR is the biggest untapped gain.** Big pages sit at position 5-8 with CTR of 0.2-2.5%.
  "RTX 5080 vs RX 9070 XT" got 293 clicks from 41,136 impressions; "What wattage for an RTX 5080"
  got 51 from 32,445, because "5080 wattage" is a one-number answer Google shows directly.

---

## 4. Rules for planning topics

1. **Name something.** Every focus keyword names a specific product, model, game or piece of
   software: "9800X3D", "RTX 5070 Ti", "Fortnite", "SolidWorks", "NVIDIA Control Panel".
   A generic keyword ("best gaming monitor", "prebuilt vs custom pc") needs a strong reason.
2. **No location modifier unless the query is local by nature.** Do not add "Bahrain", "BHD",
   "Gulf", "Dubai", "Saudi" etc. to a keyword. Use them only when the searcher's intent is
   local: price, where to buy, delivery, warranty, repair. Localize inside the article instead.
3. **Favour these proven shapes:**
   - Model vs model on current hardware - "RTX 5070 Ti vs RX 9070 XT"
   - Best [part] for [specific CPU/GPU] - "best AIO for 9800X3D"
   - [Game] at [FPS target] PC build - "Fortnite 240 FPS"
   - [Software] best settings - "NVIDIA Control Panel", "AMD Adrenalin"
   - PC for [named pro software] - MSFS, SolidWorks, DaVinci Resolve, Blender, CFD/FEA
4. **Prefer decision queries over one-number fact queries.** "5080 wattage" is answered on the
   results page and nobody clicks.
5. **Check the whole site before adding a topic, not just calendar.json.** About 87 posts predate
   the pipeline and are not in the calendar. Overlaps already exist ("how much RAM" twice,
   9800X3D twice, Blender twice). Never duplicate a top-20 page - write its sibling instead
   (NVIDIA Control Panel -> AMD Adrenalin; best AIO for 9800X3D -> best AIO for 9950X3D).
   Pull the post list from https://greypc.net/post-sitemap.xml.
6. **Every month, include 3-5 siblings of the current top 10.**

## 5. Rules for writing

1. **seo_title: lead with the product names as people search them, then the question.** Keep
   "Grey PC" at the end. Cut filler words ("Ultimate", "Definitive") before cutting the product.
2. **meta_description: give the verdict and a reason to click**, e.g. which one wins for which
   buyer, and what else the article settles (pairing, PSU, cooling). No invented numbers.
3. **Comparisons get an HTML table** - rows for use case, strengths, weaknesses and who should
   buy each. No invented benchmarks or prices; describe tiers and trade-offs.
4. **FAQ questions use the product names**, phrased the way people search:
   "Is the RX 9070 XT better than the RTX 5080 at 1440p?", not "Which GPU is better?"
5. **Localize inside, not in the keyword.** One short section on buying or building in Bahrain -
   heat, availability, warranty, Grey PC's build service - then the call to action. That is where
   the local customer is won.
6. **Do not pad.** Hit 1,300 words with substance; the data shows length does not rank a page.

## 6. Open tests (not rules yet)

- **Arabic.** A 207-word Arabic page is #5 on the site. Arabic versions of the top performers may
  reach GCC readers with little competition. One data point - worth a small test.
- **Retitling the top 10.** Rewriting seo_title and meta_description on pages already at
  position 5-8 is the cheapest traffic available. Measure CTR 28 days before and after.
