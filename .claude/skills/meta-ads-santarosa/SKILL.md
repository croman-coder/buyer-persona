---
name: meta-ads-santarosa
description: Use when creating, launching, or building Meta (Facebook/Instagram) ad campaigns for the Santa Rosa team and its brands via the Supermetrics ad-management API (platform FA). Trigger whenever the user shares a flyer, image, or ad copy and wants ads built in Meta — especially lead-form (formularios / OUTCOME_LEADS) campaigns, but also traffic, engagement, sales, or awareness objectives. Use even if the user just says "creá la pauta", "subí este flyer", "armá el anuncio de [marca]", or names a Santa Rosa brand. Handles account/page lookup, lead-form selection, ad-set targeting and budget, creative upload, and always creates PAUSED for human review.
---

# Meta Ads — Santa Rosa

Build high-performing Meta ad campaigns for Santa Rosa brands through the Supermetrics ad-management API. Platform code is `FA` (Facebook/Meta, covers Instagram placements too).

The goal is not just to *create* a campaign — it is to create one that actually performs against its objective. For lead campaigns that means **real, qualified leads**, not cheap junk form-fills. Every choice below (objective, optimization goal, form type, targeting, budget) is in service of that.

## Operating rules

1. **Always create PAUSED.** The API forces `status: PAUSED` on create — good. Never flip a campaign to `ENABLED` yourself. After building, show the user a summary + all IDs and let them activate in Meta. Only run `campaign_update status=ENABLED` if the user *explicitly* confirms in that turn.
2. **Use the user's copy verbatim.** The user supplies the headline and primary text. Load it exactly as given — do not rewrite, "improve", or translate it unless asked. If copy is missing for a required field, ask for it; don't invent it.
3. **Use fixed brand IDs.** Account IDs, Page IDs, and saved lead-form IDs live in `references/brands.md`. Read that file to resolve a brand → IDs. If a brand isn't listed, see "Resolving a new brand" below.
4. **One brand = one ad account.** Never mix brands in a campaign. Confirm which brand before building.

## Workflow

Follow these steps in order. Don't skip the confirmation step — a wrong account or form means wasted spend.

### 1. Identify brand + objective
- Resolve the brand from `references/brands.md` → `account_id`, `page_id`, default lead-form.
- Default objective is **leads** (`OUTCOME_LEADS`) unless the user says otherwise. Map other intents:
  | User wants | `objective` |
  |---|---|
  | leads / formularios | `OUTCOME_LEADS` |
  | tráfico / clicks al sitio | `OUTCOME_TRAFFIC` |
  | ventas / compras | `OUTCOME_SALES` |
  | mensajes / interacción | `OUTCOME_ENGAGEMENT` |
  | reconocimiento / alcance | `OUTCOME_AWARENESS` |

### 2. Get the creative ready
- If the user gave a flyer as a public URL → pass it as `asset_url` in the ad's `creative.assets`.
- If it's a local file or they want to browse/generate → use `resources_manage` (action `browse_assets`) to upload first, then use the returned ref/id.
- Flyers are usually 1:1 or 4:5 (feed) or 9:16 (stories). If the user gives one image, a single-image ad is fine. If they give multiple sizes, pass them all in `assets` (max 10) so Meta picks the best per placement.

### 3. Build the campaign object
Construct a single `campaign_create` call (`ds_id="FA"`) with campaign → ad set → ad nested. See `references/meta-api.md` for the exact field placement of lead forms, page_id, budget mode (CBO vs ABO), and optimization goals — **read it before your first build of a session**, the lead-form wiring is the #1 thing that goes wrong.

Key effectiveness levers (detailed in `references/meta-api.md`):
- **Lead quality:** for OUTCOME_LEADS, prefer a higher-intent instant form (review step / extra qualifying question) and set the ad-set `optimization_goal` appropriately. Tight, relevant targeting beats broad for lead *quality*.
- **Targeting:** set `locations` to the brand's real service area (don't leave it national if the business is local), sensible `age_min`/`age_max`, and exclude existing leads via `excluded_custom_audiences` when a list exists.
- **Budget:** size it so the ad set can realistically exit the learning phase (~50 optimization events/week). Confirm the daily/lifetime amount with the user; don't guess silently.

### 4. Confirm before sending
Before the `campaign_create` call, show the user a compact summary: brand, account, objective, budget, targeting, lead form, and the exact copy. Get a yes. This is cheap insurance against a wrong-account launch.

### 5. Create + report
- Call `campaign_create`. Read the `notes` array in the response — it explains ignored fields and platform limits. Surface anything important.
- If partial success (campaign created but ad set/ad failed), report the `campaign_id` and what failed; fix and retry with `campaign_update` rather than creating a duplicate.
- Report back: campaign/ad set/ad IDs, status (PAUSED), and a one-line "review & activate in Meta" reminder. If ads come back with a review status (IN_REVIEW / DISAPPROVED), mention it.

## Resolving a new brand
If the brand isn't in `references/brands.md`:
1. Ensure FA is authenticated (the user logs in via the Supermetrics link from `data_source_discovery` if needed).
2. Run `accounts_discovery` (ds_id=FA, filter by brand/Santa Rosa) to get the `account_id`.
3. Run `campaign_and_resource_get` with `resource_type: pages` to get the `page_id`, and check existing lead forms.
4. Add the brand to `references/brands.md` so it's fixed for next time, then continue the workflow.

## What good looks like
- Right account + right page, every time (no cross-brand mix-ups).
- Objective matches intent; lead campaigns optimized for *qualified* leads.
- Copy loaded exactly as the user wrote it.
- Created PAUSED, summarized clearly, user activates.
