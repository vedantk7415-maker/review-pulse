# Review Pulse 📊

A multi-page Streamlit product that turns 12,651 real Groww Play Store reviews into a
weekly product pulse — with a human approval gate before anything is published.

Every number on every page is computed in code at runtime from the real data files.
Nothing is hardcoded, nothing is invented.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at <http://localhost:8501>. No secrets are required to browse the app — the data
pages work out of the box. Secrets are only needed if you want publishing to point at
*your own* n8n instance (see below).

## Data files (do not modify)

| File | What it is |
|---|---|
| `Reviews CSV sample.csv` | 12,651 reviews (29 Jul – 20 Oct 2026): `date, rating, review_text` |
| `output.json` | The weekly analysis: top themes, pulse text, fee issue, bullets, sources, email subject/body |
| `weekly_pulse.md` | The weekly pulse deliverable (rendered + downloadable, 220 words ≤ 250) |
| `fee_explainer.md` | Customer-facing fee clarification (6 bullets, 2 sources, "Last checked") |

## Bring your own reviews CSV

On **Approve & Publish** there is a **Data source** uploader at the top:

- Pick a CSV and it is analysed **immediately** — no second button.
- Columns required: `date` (`YYYY-MM-DD HH:MM:SS`), `rating`, `review_text`.
- **Click the X on the file** to go back to the bundled sample.
- A caption always states which file is active and how many reviews were read, e.g.
  *"Analysing 12651 reviews from Reviews CSV sample.csv (bundled sample)."*
- An invalid CSV is rejected with a readable message and leaves the previous data
  source active — it can never break the page.

The CSV drives the **computed** parts of the app (reviews analysed, theme ranking,
trend, explorer, fee mention counts). The **published** content (pulse text, fee issue
headline) comes from `output.json`, which is frozen so that the Approve preview is
always exactly what gets published.

## Pages

- **Home** — KPI cards (reviews analysed, top issue, fee topic, last publish), pain
  ranking by 1–2★ volume, and an MCP/n8n connection card with **Check connection**.
- **Insights** — theme table (reviews, share, avg ★, 1–2★ count, problem rate), ranking
  rule shown, 4-week trend, one verbatim representative quote per theme (picked by code
  from the CSV, PII masked), fee panel (mentions, "charges high" vs "confused"), review
  explorer with theme tabs, text search, star filter, sort, pagination, and a weekly bar
  chart.
- **Weekly Pulse** — the pulse text with a live word counter (≤ 250) and a download.
- **Fee Explainer** — the misunderstanding, ≤ 6 bullets, 2 source links, "Last checked",
  download.
- **Approve & Publish** — the exact Google-Doc append preview + Gmail draft preview
  (labelled *Gmail draft, not sent*), checks passed/total, and a deliberate human gate:
  type **APPROVE** to enable the publish button. There is also a Reject button.
- **History** — every approve/reject with timestamp, action, fingerprint, and result
  (stored in local `history.json`, which is gitignored).
- **Checks** — 10 automated checks, all computed from the real files: ≤ 5 themes, top 3
  identified, 3 pulse quotes verbatim in the CSV, pulse ≤ 250 words, ≤ 6 fee bullets,
  exactly 2 sources, "Last checked" present, explainer matches the fee issue, email
  subject format, and no auto-send call anywhere in the source.

## Publishing (the human gate)

**Approve & Publish** is the only place anything leaves the app:

```
Review Pulse app  --(you type APPROVE)-->  n8n MCP Server Trigger
                                             ├─ append_to_doc      → Google Docs append
                                             └─ create_email_draft → Gmail DRAFT (never sent)
```

The app talks to the MCP endpoint over streamable HTTP (`mcp_client.py`): a handshake,
then `append_to_doc`, then `create_email_draft`. If no MCP endpoint is configured or it
is unreachable, it falls back to POSTing the same payload to an n8n **webhook**
(`Groww Weekly Pulse (approval-gated)`). **Neither path ever sends an email** — the Gmail
node creates a draft only, and one of the 10 checks fails the build if a send call ever
appears in the source.

### Point it at your own n8n instance

Nothing is hardcoded to a private instance in the committed code except a documented
public default. Override it either way below (both `.env` and
`.streamlit/secrets.toml` are gitignored):

| Setting | `st.secrets` key | Env var | Purpose |
|---|---|---|---|
| MCP endpoint | `N8N_MCP_URL` | `N8N_MCP_URL` | MCP Server Trigger URL (preferred path) |
| Webhook fallback | `N8N_WEBHOOK_URL` | `N8N_WEBHOOK` | n8n webhook URL (fallback path) |

Example `.streamlit/secrets.toml`:

```toml
N8N_MCP_URL = "https://your-instance.app.n8n.cloud/mcp/review-pulse"
N8N_WEBHOOK_URL = "https://your-instance.app.n8n.cloud/webhook/pulse"
```

`n8n_workflow.json` is a reference copy of the webhook fallback workflow. Replace the
`YOUR_*` placeholders with your own Doc ID, email, and credential IDs before importing.

### Security notes

- The MCP endpoint is a URL, not a credential. It can only append to a Doc and create a
  Gmail draft; it cannot send mail.
- No Doc ID, email address, or credential ever appears in the UI.
- Reviews shown in the app are masked by code: emails → `[email]`, phone-like numbers →
  `[phone]`, social handles → `[handle]`, title-prefixed names (Mr/Mrs/Dr/…) → `[name]`.

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (secrets are gitignored, so nothing sensitive goes up).
2. Create the app pointing at `app.py`.
3. Add `N8N_MCP_URL` (and optionally `N8N_WEBHOOK_URL`) under **Secrets**.

## UI notes

- The theme is locked to light via `.streamlit/config.toml`, so the custom CSS cannot be
  broken by a dark-mode toggle.
- `toolbarMode = "minimal"` keeps the toolbar menu available — press **F** (or ⋮ →
  Fullscreen) for a clean full-screen view when recording a demo.

## Repo layout

```
app.py                  # navigation shell
analysis.py             # data layer: parse, aggregate, mask, checks, payload, history
mcp_client.py           # MCP client (handshake → append_to_doc → create_email_draft)
styles.py               # shared CSS / card helpers
views/                  # one module per page (home, insights, pulse, explainer, approve, history, checks)
.streamlit/config.toml  # light theme, minimal toolbar
n8n_workflow.json       # reference copy of the webhook fallback workflow
requirements.txt
```

## Suggested demo-video flow

1. **Home** — KPI cards and the pain ranking.
2. **Insights** — theme table, trend, quotes, then the explorer with a filter applied.
3. **Data source** — upload your own CSV and show the caption update.
4. **Weekly Pulse** / **Fee Explainer** — rendered output and word count.
5. **Checks** — 10/10 passed.
6. **Approve & Publish** — previews, type APPROVE, publish, success message.
7. **History** — the action recorded.
8. **n8n** — execution history showing the Doc append and the Gmail draft.
