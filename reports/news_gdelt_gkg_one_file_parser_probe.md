# GDELT GKG One-File Parser Probe

- Status: `blocked_requires_enrichment_or_policy`
- Selected file: `20240128221500.gkg.csv.zip`
- Trade date: `2024-01-29`
- Decision time ET: `2024-01-29T09:30:00-05:00`
- Raw ZIP path: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\data\raw\spy_0dte\news\gdelt_bulk_probe\20240128221500.gkg.csv.zip`
- Raw ZIP SHA256: `5228f882e0fc4477a74b732b76df6e350ccbfddd488c38798de0360332277dec`
- Parsed rows: `605`
- HTTPS URL rows: `598`
- Non-empty source rows: `605`

## Field Mapping

| Canonical field | Status | Source | Note |
|:--|:--|:--|:--|
| `decision_time_et` | `pass` | `manifest item decision_time_et` | Decision timestamp comes from the pre-existing candidate-day command plan. |
| `fetched_at_et` | `surrogate_only` | `GKG DATE / file timestamp` | Usable only as GDELT seen/index time, not as exact fetch replay time. |
| `published_at_et` | `surrogate_only` | `GKG DATE / file timestamp` | Publication time is not proven by this field. |
| `source_name` | `pass` | `source_common_name` | Maps to the canonical source name when non-empty. |
| `url` | `pass` | `document_identifier` | Canonical importer currently accepts HTTPS URLs. |
| `headline` | `blocked` | `not present as verified GKG column` | URL slug can be a diagnostic surrogate only; do not import it as a real headline. |
| `topic` | `blocked` | `themes/v2_themes` | Project topic mapping must be pre-registered before canonical import. |

## Blockers

- `gkg_has_no_verified_headline_field`
- `gkg_publication_time_is_surrogate_not_exact`
- `gkg_topic_mapping_not_pre_registered`

## Sample Rows

- `japantoday.com` `2024-01-28T22:15:00Z` `https://japantoday.com/category/crime/update1-bombing-fugitive-worked-for-decades-at-building-contractor`
- `wfaa.com` `2024-01-28T22:15:00Z` `https://www.wfaa.com/article/news/crime/fort-worth-texas-west-7th-police-case-chase-saturday-night-january-2024/287-eccc16c1-069d-4a24-a901-94c3adc01643`
- `indiatimes.com` `2024-01-28T22:15:00Z` `https://timesofindia.indiatimes.com/city/dehradun/tiger-kills-woman-near-corbett-2nd-in-2-days-latest-news/articleshow/107210837.cms`
- `fox23.com` `2024-01-28T22:15:00Z` `https://www.fox23.com/news/a-quiet-weekend-at-the-box-office-with-the-beekeeper-on-top-and-some-oscar/article_c62ebe9e-598c-5f8b-9c5f-e702148fe407.html`
- `morningjournal.com` `2024-01-28T22:15:00Z` `https://www.morningjournal.com/2024/01/28/friendship-apl-accepting-raffle-item-donations-for-annual-wags-to-riches/`
- `hot1077radio.com` `2024-01-28T22:15:00Z` `https://www.hot1077radio.com/news/saweetie-drops-new-single-immortal-freestyle/`
- `ndtv.com` `2024-01-28T22:15:00Z` `https://www.ndtv.com/world-news/xi-jinpings-break-new-ground-message-to-france-days-after-emmanuel-macrons-india-visit-4950225`
- `barryanddistrictnews.co.uk` `2024-01-28T22:15:00Z` `https://www.barryanddistrictnews.co.uk/news/national/uk-today/24080134.holly-willoughby-apologises-swearing-dancing-ice/`
- `scmp.com` `2024-01-28T22:15:00Z` `https://www.scmp.com/comment/opinion/article/3249803/amid-rising-tensions-across-taiwan-strait-asean-has-tread-carefully`
- `theadvocate.com.au` `2024-01-28T22:15:00Z` `https://www.theadvocate.com.au/story/8499984/top-attractions-in-zeehan-tasmania-as-rated-by-visitors/?cs=2605`

## Next Step

Do not broad-download GKG files yet. Decide whether to enrich this one-file GKG probe through a source page/title fetch, a GDELT DOC API join, or another timestamp-clean news source; then rerun canonical import/audit only if verified headlines and timestamp policy pass.
