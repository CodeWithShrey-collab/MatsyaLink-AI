# MatsyaLink AI consumer guide and project deliverable

**Product:** MatsyaLink AI  
**Audience:** Fishers, cooperatives, market facilitators, buyers, mentors, judges,
and demonstration operators  
**Mission:** Improve small-scale artisanal fisher access to marine resources and
markets in support of UN Sustainable Development Goal 14.b  
**Prototype status:** Demonstration-ready; not a binding trading or payment system

## 1. Product summary

MatsyaLink AI helps a fisher decide where and how to sell a catch. The fisher
enters basic catch information once. The agent then checks the submission,
estimates freshness and urgency, searches stored market and buyer records,
compares eligible buyers, and recommends one of three actions:

1. **Direct sale** when a suitable buyer meets the fisher's expected price.
2. **Negotiate** when buyers exist but the best offer is below expectation.
3. **Alternate market** when no eligible buyer is available.

For a direct sale, the system prepares a professional offer and can send it to
the buyer. Every result is stored and contributes to the analytics dashboard.

### One-sentence value proposition

MatsyaLink turns fragmented price, demand, buyer, distance, and freshness data
into a fast, explainable next action for an artisanal fisher.

## 2. The problem MatsyaLink addresses

Small-scale fishers may have limited time to sell a perishable catch and may not
have immediate access to:

- multiple buyer offers;
- current market prices;
- reliable demand information;
- clear comparisons between price and travel cost;
- professional communication with institutional buyers;
- records showing which markets and buyers work best over time.

MatsyaLink brings these inputs into one auditable workflow. It does not guarantee
a sale, but it reduces the effort needed to identify and explain a recommended
path.

## 3. Intended users

### Fisher

Submits a catch and receives a recommended action, expected revenue, and reason.

### Cooperative or field facilitator

Operates the application on behalf of fishers, maintains accurate records, and
helps execute negotiation or transport recommendations.

### Buyer

Receives a structured catch offer containing quantity, location, price,
freshness, and estimated order value.

### Program manager

Uses the dashboard to understand volumes, outcomes, fish categories, and market
or buyer utilization.

### Demonstration operator

Runs prepared scenarios for a hackathon, internship review, or stakeholder
presentation without requiring live credentials.

## 4. What is included

| Capability | Included |
|---|---:|
| Catch submission | Yes |
| Input validation | Yes |
| Freshness classification | Yes |
| Urgency classification | Yes |
| Market retrieval | Yes |
| Buyer retrieval | Yes |
| Explainable ranking | Yes |
| Conditional action selection | Yes |
| Negotiation recommendation | Yes |
| Alternate-market fallback | Yes |
| Professional buyer email | Yes |
| Gmail SMTP support | Yes |
| Google Sheets storage | Yes |
| Local credential-free demo | Yes |
| Analytics dashboard | Yes |
| Historical sample data | Yes |
| Automated scenario tests | Yes |

## 5. What is not included

The prototype does not provide:

- payment collection;
- a legally binding sale agreement;
- buyer acceptance confirmation;
- delivery or vehicle booking;
- live GPS distance calculation;
- authentication or private user accounts;
- government permits or regulatory advice;
- catch certification;
- live auction functionality;
- a mobile application;
- guaranteed price accuracy.

Operators must explain these boundaries when using the application with real
stakeholders.

## 6. Quick start for a demonstration

### First-time preparation

From a PowerShell terminal in the project folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### Start the product

```powershell
streamlit run templates/frontend.py
```

Open the local URL printed by Streamlit, normally:

```text
http://localhost:8501
```

The default mode uses demonstration records and does not send real email. No
Gemini, Google, or Gmail credential is needed for the first run.

### Stop the product

Return to the terminal and press `Ctrl+C`.

## 7. Navigation

The left sidebar contains four pages.

```text
Catch Submission
      ↓
Agent Analysis
      ↓
Market Recommendations
      ↓
Analytics Dashboard
```

The sidebar also shows the active operating mode:

- `Data: Local demo CSV` or `Data: Google Sheets`
- `Reasoning: Deterministic demo policy` or `Reasoning: Gemini`

## 8. Page 1 — Catch Submission

### Purpose

Enter the fisher and catch information and start the autonomous analysis.

### Field guide

| Field | What to enter | Example | Why it matters |
|---|---|---|---|
| Fisher Name | Fisher's full or commonly used name | Anita Naik | Identifies the submission |
| Contact Number | Reachable phone number | +91-9876501001 | Supports follow-up |
| Location | Landing or pickup locality | Margao, Goa | Communicates pickup point |
| Fish Type | Select one available category | Mackerel | Filters markets and buyers |
| Quantity | Catch weight in kilograms | 250 | Checks capacity and revenue |
| Catch Date | Date the catch was landed | Today's date | Determines freshness |
| Catch Time | Approximate landing time | Two hours ago | Determines freshness and urgency |
| Expected Minimum Price | Lowest desired INR per kg | 280 | Separates direct sale from negotiation |
| Maximum Travel Distance | Farthest acceptable distance in km | 40 | Removes distant markets and buyers |

### Submission tips

- Enter quantity in kilograms, not crates or tonnes.
- Enter price per kilogram, not the total catch value.
- Use the actual catch time; freshness materially affects matching.
- Set a realistic travel distance the fisher can manage.
- Verify the phone number before submitting because it is persisted.
- If the fish category is absent, an operator must add it to the data and UI.

### What appears after submission

The page displays a live execution trace. Depending on the route, it includes:

- Submission Validation
- Freshness Analysis
- Urgency Analysis
- Market Retrieval
- Buyer Retrieval
- Buyer Scoring
- Decision
- Proposal Generation
- Notification for direct sales only
- Persistence
- Response

The final message gives the decision, rationale, expected revenue, recommended
action, and trace ID.

## 9. Page 2 — Agent Analysis

### Purpose

Review how the agent reached its result.

### Summary indicators

| Indicator | Meaning |
|---|---|
| Freshness | Time-based catch condition used for matching |
| Urgency | How quickly a sale should be pursued |
| Buyers Found | Number of retrieved eligible buyer records |
| Expected Revenue | Estimated value for the selected action |

### Freshness classifications

| Classification | Prototype rule | Interpretation |
|---|---|---|
| Fresh | Up to 6 hours old | Strongest compatibility |
| Moderate | More than 6 up to 12 hours | Sale should progress promptly |
| Low Freshness | More than 12 hours | Urgent handling and limited compatibility |

Freshness is a software classification, not a laboratory or food-safety
assessment. Operators remain responsible for safe handling and inspection.

### Urgency classifications

| Classification | Typical cause |
|---|---|
| Low | Fresh catch under 300 kg |
| Medium | Moderate freshness or at least 300 kg |
| High | Low freshness or at least 750 kg |

### Buyer-ranking table

Each buyer row contains:

- buyer name;
- total score out of 100;
- price score;
- distance score;
- demand score;
- capacity score;
- freshness compatibility score;
- expected revenue;
- plain-language scoring rationale.

The first row is normally the preferred buyer. A buyer with zero freshness
compatibility cannot be selected even when its total score is otherwise strong.

### Execution log

The execution log is the product's audit trail. For support, record the trace ID
and the first node marked as failed or producing an unexpected count.

## 10. Page 3 — Market Recommendations

### Purpose

Turn the decision into an actionable next step.

### Direct sale view

Shows:

- the selected buyer;
- offer and expected revenue;
- selected market context;
- the generated buyer email;
- notification status.

The fisher or facilitator should still confirm collection, quality, final price,
and payment terms.

### Negotiation view

Shows:

- the best retrieved buyer;
- buyer's listed offer;
- fisher's target price;
- a suggested negotiation strategy.

No buyer email is sent on this route. This prevents an offer below the fisher's
minimum from being treated as accepted.

### Alternate-market view

Shows:

- why no eligible buyer was selected;
- the best retrieved market;
- market price, demand, location, and distance;
- other eligible market records.

The market recommendation is based on stored data and must be checked for
current opening hours, transport feasibility, and actual arrival price.

## 11. Page 4 — Analytics Dashboard

### Purpose

Show how the marketplace performs across stored executions.

### Metrics

| Metric | Consumer interpretation |
|---|---|
| Total Catches Processed | Number of recorded agent executions |
| Average Revenue | Average expected—not confirmed—revenue |
| Total Expected Revenue | Sum of all stored estimates |
| Success Rate | Percentage routed to direct sale |
| Negotiation Rate | Percentage requiring negotiation |
| No Buyer Rate | Percentage sent to alternate markets |
| Most Requested Fish Types | Submission frequency by fish category |
| Buyer Utilization | How often each buyer was selected |
| Market Utilization | How often each market was selected |

The dashboard includes ten historical sample transactions on first launch. New
runs are appended and the next dashboard refresh includes them.

### Responsible interpretation

- Revenue is an estimate, not money received.
- Direct sale means a suitable offer was identified, not that a buyer accepted.
- High buyer utilization can indicate a good partner or overdependence.
- A high negotiation rate can indicate expectations above available offers.
- A high no-buyer rate can reveal missing buyer coverage or restrictive travel
  distances.

## 12. Understanding the three decisions

### Decision A — Direct Sale

The system chooses this route when:

- at least one eligible buyer exists;
- the selected buyer is freshness-compatible;
- the selected buyer's offer meets or exceeds the fisher's minimum.

Actions:

1. Select buyer.
2. Calculate expected revenue.
3. Generate professional offer.
4. Send or preview email.
5. Store transaction.
6. Present the result.

### Decision B — Negotiate

The system chooses this route when:

- an eligible, freshness-compatible buyer exists;
- the selected buyer's offer is below the fisher's minimum.

Actions:

1. Identify the strongest candidate.
2. Calculate the price gap.
3. Recommend a target and strategy.
4. Do not email the buyer automatically.
5. Store transaction.
6. Present the result.

### Decision C — Alternate Market

The system chooses this route when no selectable buyer exists after stored type,
demand, distance, capacity, and freshness checks.

Actions:

1. Select the best eligible retrieved market.
2. Estimate market-based revenue.
3. Recommend market travel or cooperative contact.
4. Store transaction.
5. Present the result.

## 13. How buyer scores work

The score combines five practical factors.

| Factor | Weight | Consumer question |
|---|---:|---|
| Price | 35% | Is the buyer's offer competitive with matching markets? |
| Distance | 25% | Is the buyer close enough for the fisher's travel limit? |
| Demand | 20% | Does the buyer currently have strong demand? |
| Capacity | 10% | Can the buyer take most or all of the catch? |
| Freshness | 10% | Is the catch acceptable to this buyer? |

The total is not a promise of sale probability. It is a consistent comparison
of retrieved candidates.

### Expected revenue

For a buyer, expected revenue is based on the smaller of catch quantity and
buyer capacity:

```text
matched quantity × buyer's stored price per kg
```

For a fallback market:

```text
catch quantity × market's stored price per kg
```

Transport cost, commission, spoilage, taxes, quality adjustments, and price
changes are not deducted.

## 14. Prepared demonstration scenarios

### Scenario 1 — High demand and successful sale route

Use:

| Field | Value |
|---|---|
| Fisher | Anita Naik |
| Location | Margao, Goa |
| Fish | Mackerel |
| Quantity | 250 kg |
| Catch time | Approximately 2 hours ago |
| Minimum price | INR 280/kg |
| Maximum distance | 40 km |

Expected result: `Direct Sale`, professional email preview, stored transaction.

### Scenario 2 — Buyer exists but price is low

Use:

| Field | Value |
|---|---|
| Fisher | Selvan Kumar |
| Location | Kasimedu, Chennai |
| Fish | Tuna |
| Quantity | 300 kg |
| Catch time | Approximately 5 hours ago |
| Minimum price | INR 700/kg |
| Maximum distance | 50 km |

Expected result: `Negotiate`, price-gap explanation, negotiation strategy, no
email.

### Scenario 3 — No buyer and market fallback

Use:

| Field | Value |
|---|---|
| Fisher | Bimal Das |
| Location | Howrah, West Bengal |
| Fish | Rohu |
| Quantity | 180 kg |
| Catch time | Approximately 8 hours ago |
| Minimum price | INR 220/kg |
| Maximum distance | 35 km |

Expected result: `Alternate Market`, Sealdah Wholesale Market recommendation,
stored transaction.

### Automated presentation check

```powershell
python scripts/run_demo.py
```

The script prints every node event and a `PASS` marker for each expected route.
It also writes the three runs to the transaction ledger.

## 15. Suggested five-minute presentation

### Minute 0–1: Problem and impact

“Small-scale fishers work with perishable inventory, fragmented buyer access,
and limited bargaining information. MatsyaLink AI supports SDG 14.b by converting
a catch submission into an explainable market action.”

### Minute 1–2: Show autonomous execution

Submit Scenario 1. Point to the live node trace and explain that retrieval,
scoring, decision, communication, and storage are separate LangGraph stages.

### Minute 2–3: Show explainability

Open Agent Analysis. Highlight the five weighted score components, selected
buyer, expected revenue, and execution log.

### Minute 3–4: Show conditional behavior

Explain or run Scenarios 2 and 3. Emphasize that the graph does not always send
email and never invents a missing Rohu buyer.

### Minute 4–5: Show outcomes and scale path

Open Analytics Dashboard. Explain Google Sheets integration, Gemini guardrails,
Gmail dry-run/live modes, and the production roadmap.

## 16. Operator setup for Google Sheets

Use this section only when the demonstration requires a real shared workbook.

### Required workbook tabs

- `Market Prices`
- `Buyers`
- `Transactions`

### Setup steps

1. Create a Google Cloud service account with Sheets API access.
2. Create a Google Sheet.
3. Share the sheet with the service-account email as Editor.
4. Place credentials outside the repository.
5. Copy `.env.example` to `.env`.
6. Configure:

```dotenv
USE_GOOGLE_SHEETS=true
GOOGLE_SHEET_ID=your_workbook_id
GOOGLE_SERVICE_ACCOUNT_FILE=C:\secure\service-account.json
```

7. Seed data:

```powershell
python scripts/seed_google_sheets.py
```

8. Restart Streamlit.

### Warning

The seeding script clears the three tabs before inserting bundled demonstration
data. Export any valuable transaction history before running it.

## 17. Operator setup for Gemini

Gemini improves the written decision explanation and negotiation strategy. The
business route remains protected by deterministic rules.

```dotenv
GEMINI_ENABLED=true
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
```

Restart Streamlit after changing these settings. The sidebar should display
`Reasoning: Gemini`.

If Gemini is unavailable, the system automatically uses deterministic policy
reasoning. Catch processing can still complete.

## 18. Operator setup for Gmail

Keep email in dry-run during initial review:

```dotenv
EMAIL_DRY_RUN=true
```

To enable live delivery:

1. Use a dedicated Gmail sender.
2. Enable two-step verification.
3. Create a Google app password.
4. Replace all demonstration `example.com` buyer addresses with approved real
   recipients.
5. Configure:

```dotenv
EMAIL_DRY_RUN=false
SMTP_USERNAME=sender@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_SENDER=sender@gmail.com
```

6. Restart the application.
7. Submit a controlled direct-sale test.
8. Confirm the transaction records `sent`.

Never enable live email while demonstration buyer addresses remain in the data.

## 19. Data maintenance guide

### Adding a market

Supply a unique market ID, market name, location, supported fish type, distance,
demand, price per kilogram, and timestamp. Use exactly `Low`, `Medium`, or `High`
for demand.

### Adding a buyer

Supply a unique buyer ID, buyer name, accepted fish types separated with `|`,
capacity, location, distance, offer per kilogram, valid email, current demand,
and freshness acceptance.

Example accepted-fish entry:

```text
Pomfret|Mackerel|Prawns
```

### Data quality rules

- Use one consistent spelling for each fish type.
- Prices must be non-negative INR/kg.
- Quantities and capacities must be kilograms.
- Distances must be kilometres.
- Email addresses must be valid.
- IDs must remain unique and stable.
- Do not silently replace a historical buyer with a different business under the
  same ID.
- Update demand and capacity before a high-stakes demonstration.

## 20. Privacy and responsible use

### Data stored

The transaction ledger can contain:

- fisher name;
- contact number;
- location;
- catch details;
- selected buyer and market;
- expected revenue;
- notification status;
- execution trace.

### Consumer responsibilities

- Obtain permission before recording a fisher's personal details.
- Explain where the information will be stored.
- Limit workbook access.
- Avoid entering real data in a public demonstration.
- Remove or anonymize records when no longer required.
- Verify buyer email consent before live messages.
- Do not treat the software's freshness label as food-safety certification.
- Do not represent expected revenue as guaranteed income.

## 21. Troubleshooting

### The page does not open

Confirm the terminal is still running and use the exact URL printed by
Streamlit. If port 8501 is occupied:

```powershell
streamlit run templates/frontend.py --server.port 8502
```

### Python cannot find a package

Activate the virtual environment and reinstall dependencies:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### The submission is rejected

Open Agent Analysis or read the final response. Correct the named fields. Common
causes are an empty name, short phone number, zero quantity, invalid catch time,
or zero travel distance.

### No markets are shown

Possible causes:

- fish type does not exactly match a stored category;
- all matching markets exceed the maximum travel distance;
- the Market Prices tab has missing or malformed columns;
- Google Sheets is enabled but contains different data.

### No buyers are shown

Possible causes:

- no buyer accepts the fish type;
- matching buyers have Low demand;
- all buyers are too far away;
- all buyer capacities are zero;
- sheet data is malformed.

### A buyer appears in ranking but is not selected

It may have zero freshness compatibility. The system displays retrieved scores
for transparency but refuses to select a completely incompatible buyer.

### Gemini is not active

Check that `GEMINI_ENABLED=true`, the API key is present, and the application was
restarted. If the call fails, deterministic reasoning is expected behavior.

### Email says dry-run

This is the safe default. Configure all SMTP values and set
`EMAIL_DRY_RUN=false` only after verifying recipients.

### Email failed

Check the Gmail app password, two-step verification, network access, SMTP
username, and sender. A failed email does not erase the match; inspect the stored
transaction and contact the buyer manually.

### Dashboard has unexpected counts

The bundled ledger contains historical demo records. Running tests does not
modify it, but using the app and `run_demo.py` does. Review the Transactions tab
or CSV for duplicate demonstration runs.

### Google Sheets data is not used

The system falls back to CSV unless all of the following are present:

- `USE_GOOGLE_SHEETS=true`;
- workbook ID;
- service-account file or JSON credentials.

Restart after changing configuration.

## 22. Frequently asked questions

### Is MatsyaLink a chatbot?

No. The primary interaction is a structured catch submission. A LangGraph agent
retrieves records, scores options, selects a route, executes tools, and persists
the outcome.

### Can the model invent a buyer?

No accepted decision may reference a buyer or market absent from retrieved
records. Model output is checked before use.

### Does the highest offered price always win?

No. Price has the largest weight, but distance, demand, capacity, and freshness
also affect the ranking.

### Does direct sale mean the sale is complete?

No. It means a stored buyer offer meets the policy and an offer can be sent.
Buyer confirmation, pickup, quality inspection, and payment happen outside the
prototype.

### Why is no email sent during negotiation?

The offered price is below the fisher's stated minimum. The system recommends a
strategy instead of implying acceptance.

### Can it work without internet?

After dependencies are installed, local CSV storage, deterministic reasoning,
and email dry-run can operate without cloud services.

### Can operators edit Google Sheets directly?

Yes, provided they preserve required columns and valid values. Changes are read
on subsequent tool calls.

### Can another currency be used?

Not without modification. The current UI and messages assume INR per kilogram.

### Is the freshness classification legally authoritative?

No. It is a time-based matching feature, not inspection or certification.

## 23. Glossary

| Term | Meaning |
|---|---|
| Artisanal fisher | Small-scale fisher using relatively small vessels or traditional methods |
| Buyer capacity | Maximum kilograms the stored buyer record can currently accept |
| Catch freshness | Prototype age-based class used for compatibility |
| Conditional route | A workflow branch selected from current state rather than always executed |
| Direct sale | Buyer offer meets the fisher's minimum; an offer may be sent |
| Dry-run | Communication is prepared but deliberately not delivered |
| Expected revenue | Calculated estimate before costs and final confirmation |
| Market reference | Average eligible market price used in buyer price scoring |
| Negotiation | Buyer exists, but stored offer is below the fisher's minimum |
| No-buyer rate | Share of executions routed to alternate markets |
| SDG 14.b | UN target concerning access for small-scale artisanal fishers to marine resources and markets |
| Trace ID | Transaction identifier used to locate a stored execution |

## 24. Consumer acceptance checklist

A stakeholder can accept the prototype deliverable when they can confirm:

- [ ] The application starts locally from documented commands.
- [ ] Catch Submission captures every requested field.
- [ ] The live view shows multiple agent execution stages.
- [ ] Scenario 1 produces Direct Sale and an email preview.
- [ ] Scenario 2 produces Negotiate and sends no email.
- [ ] Scenario 3 produces Alternate Market using a stored market.
- [ ] Buyer scoring displays all five weighted factors.
- [ ] No result contains an invented buyer.
- [ ] Every run receives a trace ID or records a storage failure.
- [ ] Dashboard data updates from the transaction ledger.
- [ ] Google Sheets, Gemini, and Gmail configuration paths are documented.
- [ ] Default operation performs no live email side effect.
- [ ] Product limitations and privacy responsibilities are disclosed.

## 25. Deliverable inventory

| Deliverable | Location |
|---|---|
| Product overview and quick start | `README.md` |
| Consumer guide | `docs/CONSUMER_DELIVERABLE.md` |
| Developer handbook | `docs/DEVELOPER_GUIDE.md` |
| Architecture reference | `docs/architecture.md` |
| Phase completion checklist | `docs/phase-checklist.md` |
| Streamlit product | `templates/frontend.py` |
| LangGraph orchestration | `graph.py` |
| Market and buyer demo data | `data/` |
| Automated demo runner | `scripts/run_demo.py` |
| Google Sheets provisioning | `scripts/seed_google_sheets.py` |
| Automated verification | `tests/` |
| Environment template | `.env.example` |

## 26. Support handoff template

When reporting a problem, provide:

```text
MatsyaLink version/date:
Operating system:
Python version:
Storage mode: CSV / Google Sheets
Reasoning mode: Deterministic / Gemini
Email mode: Dry-run / Live
Trace ID:
First unexpected node:
Displayed error:
Expected behavior:
Steps to reproduce:
```

Do not include API keys, SMTP passwords, or service-account JSON in a support
request.

