# Meta (FA) — campaign_create wiring & gotchas

How to assemble a `campaign_create` call for Meta. `ds_id="FA"`. Structure is
campaign → `ad_groups` (= ad sets in Meta) → `ads`.

## Table of contents
- [Skeleton](#skeleton)
- [Campaign level](#campaign-level)
- [Budget: CBO vs ABO](#budget-cbo-vs-abo)
- [Ad set level](#ad-set-level)
- [Lead forms (formularios)](#lead-forms-formularios)
- [Ad / creative level](#ad--creative-level)
- [Targeting](#targeting)
- [Lead quality levers](#lead-quality-levers)
- [Common failures](#common-failures)

## Skeleton
```
campaign_create(
  ds_id="FA",
  account_id="act_...",            # from brands.md
  name="Marca | Leads | 2026-06 | v1",
  platform_settings={
    "objective": "OUTCOME_LEADS",
    "campaign_budget_optimization": false   # false = ABO (budget per ad set)
  },
  ad_groups=[{
    "name": "Marca | AdSet | <audiencia>",
    "budget_amount": 5000,
    "budget_type": "DAILY",
    "platform_settings": {
      "page_id": "...",                 # REQUIRED for lead ads
      "optimization_goal": "LEAD_GENERATION",
      "billing_event": "IMPRESSIONS"
    },
    "targeting": { ... },               # see Targeting
    "ads": [{
      "name": "Marca | Ad | v1",
      "platform_settings": { "page_id": "..." },   # REQUIRED
      "creative": {
        "headlines": ["<titular EXACTO del usuario>"],
        "descriptions": ["<texto primario EXACTO del usuario>"],
        "call_to_action": "SIGN_UP",
        "lead_gen_form_id": "...",       # REQUIRED for OUTCOME_LEADS
        "assets": [{ "asset_url": "https://.../flyer.jpg" }]
      }
    }]
  }]
)
```

## Campaign level
- `platform_settings.objective`: one of `OUTCOME_LEADS`, `OUTCOME_TRAFFIC`, `OUTCOME_SALES`, `OUTCOME_ENGAGEMENT`, `OUTCOME_AWARENESS`.
- `status` is always created PAUSED — don't try to override.

## Budget: CBO vs ABO
- `campaign_budget_optimization: false` → **ABO**: put `budget_amount` + `budget_type` on each **ad set** (`ad_groups[i]`), NOT on the campaign.
- `campaign_budget_optimization: true` → **CBO**: put budget at **campaign** level; Meta distributes across ad sets.
- Default to ABO for a single-ad-set lead campaign — simplest, predictable spend.
- `budget_type`: `DAILY` or `LIFETIME`. LIFETIME requires `end_date` (YYYY-MM-DD).

## Ad set level (`ad_groups[i]`)
`platform_settings`:
- `page_id` — **required** for lead ads (the form lives on this Page).
- `optimization_goal` — for leads use `LEAD_GENERATION`. (Optimizing for "conversion leads"/quality requires a CRM integration configured in Meta; if the team has it, that's set up Meta-side, not here.)
- `billing_event` — usually `IMPRESSIONS`.
- `status` — leave default.

## Lead forms (formularios)
This is the #1 thing that breaks. For `OUTCOME_LEADS`:
- The ad's `creative.lead_gen_form_id` MUST be set to an existing instant-form ID.
- The `page_id` MUST be present on **both** the ad set and the ad `platform_settings`, and it must be the Page that owns the form.
- Get available forms: the saved default is in `brands.md`. To list/verify, use
  `campaign_and_resource_get` with `resource_type: pages` (and check the Page's forms) — forms are created in Meta's Lead Center, not via this API.
- If no form exists yet, the user must create one in Meta first; this API consumes a form, it doesn't build one.

## Ad / creative level
- `headlines[0]` → the ad **headline/title**. `descriptions[0]` → the **primary text** (cuerpo). Load both exactly as the user supplied.
- `call_to_action`: pick the button matching intent. Leads → `SIGN_UP`, `LEARN_MORE`, `GET_QUOTE`, `CONTACT_US`, `SUBSCRIBE`, `APPLY_NOW`, `BOOK_TRAVEL`. Ask the user if unsure.
- `assets`: array of `{asset_url}` (public URL), `{asset_id}` (already in account), or `{upload_ref}` (from `resources_manage`). One item = single image. Up to 10 = Meta picks best per placement.
- For a placement-optimized ad, give multiple aspect ratios (1:1 feed, 9:16 stories). One flyer is fine for a quick single-image ad.

## Targeting (`ad_groups[i].targeting`)
- `locations`: country codes or names — **set the brand's real service area**, not national, for a local business. This is the biggest lead-quality lever.
- `age_min` / `age_max`, `genders` (`MALE`/`FEMALE`).
- `interests` / `custom_audiences` / `lookalike_audiences`: `{id, name}` objects. Look them up with `campaign_and_resource_get` `resource_type: targeting_search` or `audiences`.
- `excluded_custom_audiences`: exclude existing leads/customers so spend goes to net-new — improves lead value.
- `expand_targeting: true` lets Meta widen beyond your set — fine for volume, but for *quality* keep it off until you have data.

## Lead quality levers (the point of these campaigns)
"Leads que sean leads" comes from, in priority order:
1. **Form intent** — a higher-intent instant form (with a review/confirmation step or an extra qualifying question) filters out accidental submits. Chosen Meta-side; pick the higher-intent form when the brand has one.
2. **Tight, relevant targeting** — correct `locations`, sensible age, exclude past leads. Broad audiences inflate volume and tank quality.
3. **Honest, specific copy** (user-provided) — pre-qualifies; vague offers attract junk.
4. **Enough budget to learn** — aim for ~50 lead events/week per ad set so Meta's optimization exits the learning phase and finds quality patterns. Too-small budget = perpetual learning = erratic quality. Quick sizing: daily budget ≈ 7 × the brand's cost per result.

## Judging results (Santa Rosa data, 2026-09-26)
Checked on 561 new contact campaigns (Jun 2025–Sep 2026, all 85 accounts; `scripts/curva_aprendizaje.py`). Our Meta curve is **flat**, unlike the external 26-week study where Advantage+ Leads drops ~80%:
- Week 1 is usually *cheaper* than weeks 3-4 (61% of campaigns, median −11%). Never judge on week 1; judge at weeks 3-4 on a 4-week average.
- Campaigns that survive barely improve: median +9% at weeks 3-4, +3% at weeks 5-8, best −13% at weeks 13-18.
- The start predicts: campaigns starting at ≥2× the brand's cost per result recovered in only 2 of 9 cases even after 8 weeks, and those starting below it stayed cheap in 34 of 41. So early cut (weeks 2-3) is justified at ≥2× the brand, or when a campaign competes with our own campaign for the same audience.
- 62% of our campaigns stop before week 5. Prefer refreshing creatives in a working ad set over launching a new campaign.
- Google (not yet connected): follow the study. Judge Search at 4-6 weeks and PMax no earlier than 6.
Full notes: vault `Investigación/📈 Curva de aprendizaje — Google Ads vs Meta (26 semanas).md` and Manual §4.4.

## Common failures
- Lead campaign with no `lead_gen_form_id` → ad fails or falls back. Always set it.
- Missing `page_id` on ad set or ad → creation error.
- Budget on campaign while ABO (`campaign_budget_optimization:false`) → ignored/misplaced; put it on the ad set.
- `LIFETIME` budget without `end_date` → rejected.
- Always read the response `notes[]` — ignored/altered fields are reported there.
- On partial success, fix with `campaign_update` using the returned `campaign_id`; don't re-create (avoids duplicates).
