# MatsyaLink AI manual feature and agentic-workflow test guide

**Audience:** Developers, QA reviewers, mentors, judges, and demonstration
operators  
**Objective:** Manually verify every user-visible feature, major internal
contract, cloud integration, conditional route, and agentic behavior  
**Expected duration:** 60–90 minutes for offline tests; longer for cloud setup  
**Last reviewed against source:** 20 July 2026

## 1. Test strategy

Use three passes:

1. **Offline acceptance pass:** CSV storage, deterministic reasoning, email
   dry-run. No credentials required.
2. **Agentic route pass:** Prove that state and evidence produce different graph
   paths and actions.
3. **Cloud integration pass:** Enable Gemma 4 through Ollama, Google Sheets, and optionally Gmail
   one at a time.

Do not enable all cloud services at once before the offline pass succeeds. A
single-integration-at-a-time sequence makes failures easy to isolate.

## 2. Does MatsyaLink have an agentic workflow?

**Yes.** MatsyaLink implements a bounded autonomous agent in LangGraph.

It satisfies the agentic cycle as follows:

| Agentic capability | MatsyaLink implementation | Evidence to observe |
|---|---|---|
| Perceive | Accept and validate catch context | Validation state and log |
| Maintain state | Typed `AgentState` across nodes | Analysis fields and ordered trace |
| Retrieve | Execute market and buyer tools | Tool names and record counts in logs |
| Reason | Score evidence and optionally invoke Gemma 4 31B Cloud | Component scores and reasoning source |
| Decide | Select direct sale, negotiation, or fallback | Decision type changes by scenario |
| Select action | Conditional LangGraph edge chooses next node | Different proposal node in trace |
| Act | Generate offer, send/preview email, persist | Notification status and transaction ID |
| Observe | Append outcome and execution details | Execution log and analytics update |

### What kind of agent is it?

It is a **bounded, goal-directed workflow agent**, not an unrestricted chat or
general-purpose ReAct agent. Retrieval and action tools are called from explicit
LangGraph nodes. The agent autonomously chooses the business route from current
state. Gemma 4 can generate structured reasoning, but deterministic guardrails
prevent it from inventing marketplace entities or accepting a below-minimum
offer.

This is agentic because execution and action selection depend on observed state,
retrieved evidence, scoring, and policy. It is not CRUD because the form does not
map directly to a stored row; a multi-stage autonomous decision occurs before
the result is written. It is not a chatbot because a conversational response is
not the orchestration mechanism.

### Important demonstration distinction

- With `OLLAMA_ENABLED=false`, the graph is still autonomous and agentic, but the
  decision explanation uses deterministic policy.
- With `OLLAMA_ENABLED=true` and working Ollama Cloud access, the trace should
  report `gemma4_guardrailed`, proving Gemma 4 participated in reasoning.
- Tool selection is graph-bounded rather than arbitrary. This is intentional for
  traceability and safe market communication.

For a final presentation claiming “Gemma 4 as the reasoning model,” run the cloud
model test and show `Reasoning source: gemma4_guardrailed` in Agent Analysis.

## 3. Test environment preparation

### 3.1 Create and activate an environment

```powershell
cd G:\Hackathons\IBM
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3.2 Create the safe offline configuration

```powershell
Copy-Item .env.example .env
```

Confirm these values in `.env`:

```dotenv
OLLAMA_ENABLED=false
USE_GOOGLE_SHEETS=false
EMAIL_DRY_RUN=true
```

Restart Streamlit after every `.env` change because configuration is cached.

### 3.3 Back up the demonstration ledger

Manual app and demo-script runs append transactions. Before testing:

```powershell
Copy-Item data\transactions.csv data\transactions.manual-test-backup.csv
```

After testing, restore it if required:

```powershell
Copy-Item data\transactions.manual-test-backup.csv data\transactions.csv -Force
Remove-Item data\transactions.manual-test-backup.csv
```

Do not restore while Streamlit is processing a submission.

### 3.4 Establish the automated baseline

```powershell
python -m compileall -q .
python -m pytest -q
```

Pass criteria:

```text
12 passed
```

### 3.5 Start the application

```powershell
streamlit run templates/frontend.py
```

Pass criteria:

- A browser page opens without a Python exception.
- The title is MatsyaLink AI.
- The sidebar reports Local demo CSV.
- The sidebar reports Deterministic demo policy.
- Four navigation choices are present.

## 4. Test evidence template

Record each manual test using:

```text
Test ID:
Date/time:
Tester:
Environment:
Input:
Expected:
Actual:
Trace ID:
Evidence captured:
PASS / FAIL:
Notes or defect ID:
```

For graph tests, capture:

- final response;
- Agentic workflow evidence panel;
- buyer ranking when present;
- execution log;
- transaction ledger row;
- dashboard before and after when relevant.

## 5. Foundation and UI tests

### MT-001 — Application startup

**Purpose:** Verify dependencies, imports, and Streamlit entry point.

Steps:

1. Start Streamlit using the command above.
2. Open the printed local URL.
3. Navigate through all four sidebar items.

Expected:

- No page crashes.
- Submission form appears.
- Analysis and Recommendations request a submission before one exists.
- Analytics displays historical metrics.
- No custom CSS or styled HTML is required.

### MT-002 — Frontend field coverage

Confirm Catch Submission contains:

1. Fisher Name
2. Contact Number
3. Location
4. Fish Type
5. Quantity
6. Catch Date
7. Catch Time
8. Expected Minimum Price
9. Maximum Travel Distance

Expected: all nine inputs and `Run MatsyaLink Agent` are visible.

### MT-003 — Page navigation and session behavior

Steps:

1. Run any successful submission.
2. Open Agent Analysis.
3. Open Market Recommendations.
4. Return to Catch Submission.

Expected:

- Analysis retains the latest result during the session.
- Recommendations retain the selected buyer/market and proposal.
- Navigation alone does not create another transaction.
- A full browser/session reset may clear the latest analysis, while persisted
  dashboard data remains.

## 6. Validation tests

### MT-010 — Valid submission normalization

Use:

```text
Fisher Name: anita naik
Contact Number: +91-9876501001
Location: Margao, Goa
Fish Type: Mackerel
Quantity: 250
Catch Time: approximately 2 hours ago
Expected Minimum Price: 280
Maximum Travel Distance: 40
```

Expected:

- Submission Validation completes.
- The graph continues to Freshness Analysis.
- Fish type is normalized as `Mackerel`.
- A generated catch ID appears in validation log details.

### MT-011 — Missing fisher name

Steps:

1. Clear Fisher Name.
2. Keep other inputs valid.
3. Submit.

Expected:

- Validation fails.
- Freshness, retrieval, scoring, decision, proposal, and notification do not run.
- The route is Validation → Persistence → Response.
- A rejected transaction is stored.
- The response names the validation problem.

### MT-012 — Invalid contact number

Enter `123` as Contact Number.

Expected: validation reports that the value is too short and the rejected route
is persisted.

### MT-013 — Input bounds

Use the UI controls to inspect quantity, price, and distance minimums.

Expected:

- Quantity cannot be below 1 in the form.
- Price cannot be negative.
- Maximum distance cannot be below 1.
- The domain model also rejects nonpositive quantity and distance when invoked
  outside the UI.

## 7. Freshness tests

Run the same Mackerel catch three times with only catch time changed.

### MT-020 — Fresh

Input catch time: 2 hours ago.  
Expected: `Fresh`; log age approximately 2 hours.

### MT-021 — Moderate

Input catch time: 8 hours ago.  
Expected: `Moderate`; log age approximately 8 hours.

### MT-022 — Low Freshness

Input catch time: 14 hours ago.  
Expected: `Low Freshness`; log age approximately 14 hours.

### MT-023 — Threshold boundaries

If precise timestamps are practical, test 6 hours and 12 hours.

Expected:

- Exactly 6 hours remains Fresh.
- More than 6 hours becomes Moderate.
- Exactly 12 hours remains Moderate.
- More than 12 hours becomes Low Freshness.

Allow a small tolerance because time passes between selection and node execution.

## 8. Urgency tests

### MT-030 — Low urgency

Use a 2-hour-old, 250 kg catch.  
Expected: `Low`.

### MT-031 — Medium urgency from quantity

Use a 2-hour-old, 300 kg catch.  
Expected: `Medium` even though freshness is Fresh.

### MT-032 — Medium urgency from freshness

Use an 8-hour-old, 180 kg catch.  
Expected: `Medium` because freshness is Moderate.

### MT-033 — High urgency from quantity

Use a 2-hour-old, 750 kg catch.  
Expected: `High`.

### MT-034 — High urgency from freshness

Use a 14-hour-old, 180 kg catch.  
Expected: `High` because freshness is Low Freshness.

## 9. Market retrieval tests

### MT-040 — Fish-type filtering

Use Rohu with a 35 km maximum distance.

Expected:

- Three Rohu market records are retrieved within the radius.
- No Pomfret, Mackerel, Prawns, or Tuna market appears.

Direct tool verification:

```powershell
python -c "from tools import get_market_prices; r=get_market_prices.invoke({'fish_type':'Rohu'}); print(len(r)); print([x['fish_type'] for x in r])"
```

Expected output includes `3` and only `Rohu`.

### MT-041 — Travel-distance filtering

Use Mackerel with a 15 km maximum distance.

Expected:

- Only the 10 km matching market is eligible.
- The 16 km and 27 km markets are removed.
- The retrieval log still distinguishes records retrieved by the tool from
  records eligible after node filtering.

### MT-042 — No eligible market

Use Mackerel with a 5 km maximum distance.

Expected: `available_markets` is empty because the closest stored Mackerel market
is farther than 5 km.

## 10. Buyer retrieval tests

### MT-050 — Accepted fish-type filtering

Use Mackerel with a 40 km maximum distance.

Expected:

- Only buyers whose accepted list contains Mackerel appear.
- No Rohu-only buyer can appear because no Rohu buyer exists in sample data.

Direct check:

```powershell
python -c "from tools import get_available_buyers; r=get_available_buyers.invoke({'fish_type':'Mackerel'}); print([(x['buyer_name'], x['accepted_fish_types']) for x in r])"
```

### MT-051 — No invented buyer

Use Rohu with a 35 km maximum distance.

Expected:

- Buyers Found is 0.
- Buyer ranking is absent or empty.
- `selected_buyer` is null.
- The system does not fabricate a cooperative or buyer name.

Direct check:

```powershell
python -c "from tools import get_available_buyers; print(get_available_buyers.invoke({'fish_type':'Rohu'}))"
```

Expected: `[]`.

### MT-052 — Buyer distance filtering

Use Mackerel with a 9 km maximum distance.

Expected: only stored Mackerel buyers at 9 km or less remain eligible. Compare
the buyer count with a 40 km run.

### MT-053 — Low demand exclusion using a controlled data edit

This test modifies demo data. Keep the backup created in Section 3.

Steps:

1. Open `data/buyers.csv` in a spreadsheet editor.
2. Choose a Mackerel buyer that normally appears.
3. Change `current_demand` from High or Medium to `Low`.
4. Save, restart Streamlit, and submit the same Mackerel catch.
5. Restore the original CSV after the test.

Expected: the modified buyer is not returned by Buyer Retrieval.

### MT-054 — Zero capacity exclusion using a controlled data edit

Repeat the process with `capacity_kg=0`.

Expected: the buyer may be returned by the tool but is removed by the retrieval
node before scoring.

## 11. Buyer scoring tests

### MT-060 — Ranking visibility

Run Scenario 1 from Section 14.

Expected: every ranking row contains:

- total score;
- price score;
- distance score;
- demand score;
- capacity score;
- freshness score;
- expected revenue;
- reasoning.

### MT-061 — Weight verification

Select one displayed buyer and calculate:

```text
price × 0.35
+ distance × 0.25
+ demand × 0.20
+ capacity × 0.10
+ freshness × 0.10
```

Expected: the sum equals the displayed total, allowing for rounding.

### MT-062 — Price score cap

Choose a buyer whose offer exceeds the market reference.

Expected: price score is capped at 100, not greater than 100.

### MT-063 — Capacity effect

Compare the same buyer using a catch below its capacity and a catch above its
capacity.

Expected:

- At or below capacity, capacity score is 100.
- Above capacity, the score falls in proportion to capacity/catch quantity.
- Expected revenue uses the capacity-limited matched quantity.

### MT-064 — Distance effect

Increase Maximum Travel Distance while holding the buyer and catch constant.

Expected: the same absolute buyer distance receives a higher normalized distance
score because it consumes less of the fisher's allowed radius.

### MT-065 — Freshness incompatibility guard

Use controlled buyer data so a strict `Fresh` buyer receives a Low Freshness
catch and no alternative compatible buyer exists.

Expected:

- Its freshness score is 0.
- It is not selected.
- The decision falls back to an alternate market.

Restore the buyer CSV after this test.

## 12. Conditional business route tests

These three tests are the strongest proof that the workflow is agentic rather
than a fixed pipeline.

### MT-070 — Direct-sale route

Input:

```text
Fisher Name: Anita Naik
Contact: +91-9876501001
Location: Margao, Goa
Fish: Mackerel
Quantity: 250 kg
Catch Time: 2 hours ago
Minimum Price: INR 280/kg
Maximum Distance: 40 km
```

Expected decision: `direct_sale`.

Expected dynamic route:

```text
submission_validation
→ freshness_analysis
→ urgency_analysis
→ market_retrieval
→ buyer_retrieval
→ buyer_scoring
→ decision_agent
→ proposal_generation through direct_sale_proposal
→ notification
→ persistence
→ response
```

Expected actions:

- Buyer selected from retrieved records.
- Email content generated.
- Notification status is `dry_run` or `sent`.
- Transaction stored.
- Expected revenue is positive.

### MT-071 — Negotiation route

Input:

```text
Fisher Name: Selvan Kumar
Contact: +91-9876501002
Location: Kasimedu, Chennai
Fish: Tuna
Quantity: 300 kg
Catch Time: 5 hours ago
Minimum Price: INR 700/kg
Maximum Distance: 50 km
```

Expected decision: `negotiate`.

Expected route difference:

```text
decision_agent → negotiation_proposal → persistence → response
```

Pass criteria:

- A retrieved buyer is selected as negotiation target.
- Explanation states the offer is below the minimum.
- Strategy is present.
- Notification node is absent from the route.
- No email payload is shown.
- Transaction is stored.

### MT-072 — Alternate-market route

Input:

```text
Fisher Name: Bimal Das
Contact: +91-9876501003
Location: Howrah, West Bengal
Fish: Rohu
Quantity: 180 kg
Catch Time: 8 hours ago
Minimum Price: INR 220/kg
Maximum Distance: 35 km
```

Expected decision: `alternate_market`.

Expected route difference:

```text
decision_agent → fallback_proposal → persistence → response
```

Pass criteria:

- No buyer is selected.
- Sealdah Wholesale Market is selected from retrieved records.
- Notification node is absent.
- Revenue uses market price × catch quantity.
- Transaction is stored.

### MT-073 — Automated three-route cross-check

```powershell
python scripts/run_demo.py
```

Expected:

```text
[PASS] High demand - successful sale: direct_sale
[PASS] Offer below expectation - negotiation: negotiate
[PASS] No buyer - alternate market: alternate_market
```

The displayed node lists must differ: only direct sale contains Notification.

## 13. Proposal and email-template tests

### MT-080 — Direct proposal contents

Open Market Recommendations after MT-070.

Expected email preview includes:

- fish type;
- available quantity;
- fisher location;
- expected minimum price;
- buyer's listed offer;
- catch freshness;
- estimated order value;
- confirmation request.

### MT-081 — Generation is separate from delivery

With `EMAIL_DRY_RUN=true`, run MT-070.

Expected:

- Complete email content exists.
- Status is `dry_run`.
- No SMTP delivery occurs.
- Persistence records the dry-run status.

### MT-082 — Negotiation does not send

Run MT-071 with live SMTP configured or dry-run.

Expected: notification is not invoked in either mode because route selection
occurs before delivery.

## 14. Persistence tests

### MT-090 — Local transaction append

Before a submission:

```powershell
(Import-Csv data\transactions.csv).Count
```

Run one valid submission, then repeat the command.

Expected:

- Row count increases by exactly one.
- The final response contains a `T-...` trace ID.
- The new row contains timestamp, submission JSON, decision, selections,
  revenue, outcome, notification status, and execution log JSON.

### MT-091 — Rejected transaction persistence

Run MT-011 and inspect the last row.

Expected:

- `decision` is `rejected`.
- `outcome` is `validation_failed`.
- Fish type may be `Unknown` when not supplied.
- Validation log is stored.

### MT-092 — JSON readability

Open the last transaction in a spreadsheet editor or inspect with PowerShell.

Expected: `submission` and `execution_log` are quoted JSON strings that can be
parsed, not Python object representations.

## 15. Analytics tests

### MT-100 — Baseline dashboard

Open Analytics Dashboard before running a new test.

Expected initial bundled values:

- Total Catches Processed: 10
- Success Rate: 60%
- Negotiation Rate: 20%
- No Buyer Rate: 20%
- Each of the five fish categories appears twice

If previous manual runs remain in the ledger, use the backed-up file to restore
this exact baseline.

### MT-101 — Dashboard update

1. Record Total Catches Processed.
2. Run one direct-sale submission.
3. Return to Analytics Dashboard.

Expected:

- Total increases by one.
- Fish-type count increases for the submitted category.
- Selected buyer and market utilization increase.
- Revenue aggregates update.
- Rates are recalculated using the larger denominator.

### MT-102 — Metric interpretation

Manually verify:

```text
success_rate = direct_sale_count / total_count × 100
negotiation_rate = negotiate_count / total_count × 100
no_buyer_rate = alternate_market_count / total_count × 100
```

Expected: dashboard percentages match the ledger. Rejected rows remain in the
total denominator.

## 16. Agentic-workflow proof tests

### MT-110 — State-dependent action selection

Run MT-070, MT-071, and MT-072 without changing the graph code.

Expected: different state and retrieved evidence produce three different
actions. This disproves a hard-coded single output path.

### MT-111 — Tool-execution evidence

In Agent Analysis, expand `Agentic workflow evidence`.

Expected:

- Tools executed includes `get_market_prices` and `get_available_buyers`.
- Tools executed also shows `calculate_buyer_score`, `save_transaction`, and
  `send_buyer_notification` when the selected route calls them.
- The execution log contains a market reference from scoring.
- Direct-sale log also contains notification and persistence outcomes.

The scoring log also reports how many score-tool calls were executed.

### MT-112 — Dynamic conditional edge evidence

Run:

```powershell
python graph.py
```

Expected Mermaid text includes:

- conditional routing after `submission_validation`;
- three destinations after `decision`;
- notification only after the direct-sale proposal;
- all branches converging on persistence.

Compare this topology with the `Dynamic route` shown in Agent Analysis.

### MT-113 — Autonomous action execution

Submit MT-070 once and do not manually select a buyer or click a separate send or
save control.

Expected: after one form submission, the agent retrieves, scores, selects,
generates, notifies in configured mode, persists, and responds autonomously.

### MT-114 — No-hallucination guard

Run the Rohu fallback scenario with Ollama disabled, then repeat with Gemma 4
enabled.

Expected in both modes:

- No buyer is invented.
- Decision remains alternate market.
- Any model output containing an unknown ID would be rejected by the decision
  node and replaced by deterministic policy.

### MT-115 — Traceability

For any run, compare the UI route, execution log, and stored execution-log JSON.

Expected:

- Node order matches.
- Decision and notification state match.
- A single transaction trace ID correlates final response and ledger.

## 17. Gemma 4 31B Cloud manual tests

These tests require a valid key and internet access.

### MT-120 — Enable Gemma 4 reasoning

Configure `.env`:

First run `ollama signin` and `ollama pull gemma4:31b-cloud`, then configure:

```dotenv
OLLAMA_ENABLED=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:31b-cloud
```

Restart Streamlit and run MT-070 or MT-071.

Expected:

- Sidebar reports Reasoning: Gemma 4 31B Cloud.
- Agentic workflow evidence reports `gemma4_guardrailed`.
- Decision log details contain `llm_used: true`.
- Business route still follows price policy.

### MT-121 — Gemma 4 cannot override a below-minimum price

With Ollama/Gemma enabled, run MT-071.

Expected: decision remains `negotiate`. A natural-language explanation may
change, but direct sale is not allowed.

### MT-122 — Ollama/Gemma fallback resilience

For direct cloud mode, temporarily configure an invalid Ollama API key. For local
proxy mode, stop Ollama temporarily. Leave `OLLAMA_ENABLED=true`, restart, and run
a valid submission.

Expected:

- Workflow completes rather than stopping.
- Reasoning source is `deterministic_policy`.
- Decision log shows `llm_used: false` and a fallback exception type.
- Correct route, persistence, and response still occur.

Restore Ollama access or disable the integration after the test.

## 18. Google Sheets manual tests

Use a disposable workbook. The seeder clears its target tabs.

### MT-130 — Provision the workbook

1. Create and share a workbook with the service-account email.
2. Configure ID and credentials.
3. Run:

```powershell
python scripts/seed_google_sheets.py
```

Expected tabs and data rows:

- Market Prices: 15
- Buyers: 20
- Transactions: header, initially no rows after seeding

### MT-131 — Switch repository adapter

Set:

```dotenv
USE_GOOGLE_SHEETS=true
```

Restart Streamlit.

Expected: sidebar reports Data: Google Sheets.

### MT-132 — Google Sheets retrieval

Run MT-070.

Expected:

- Markets and buyers match workbook contents.
- Editing a buyer price in the sheet changes scoring on the next submission.
- No application restart is needed for ordinary row-value changes.

### MT-133 — Google Sheets persistence

After a submission, open Transactions.

Expected: one new row with the same trace ID as the final response.

### MT-134 — Permission failure

Remove workbook access from the service account or use a wrong sheet ID in a
controlled test, then restart.

Expected: retrieval fails visibly. Unlike Gemma/Ollama and SMTP, storage retrieval does
not currently have a silent CSV fallback once Google Sheets is fully configured.
Restore permissions before continuing.

## 19. Gmail SMTP manual tests

Use a dedicated test sender and an approved recipient. Replace sample
`example.com` buyer emails before this section.

### MT-140 — Dry-run safety

With `EMAIL_DRY_RUN=true`, run MT-070.

Expected: complete preview and `dry_run`; no mailbox receives a message.

### MT-141 — Live delivery

Configure:

```dotenv
EMAIL_DRY_RUN=false
SMTP_USERNAME=sender@gmail.com
SMTP_PASSWORD=google_app_password
SMTP_SENDER=sender@gmail.com
```

Restart and run a controlled direct-sale submission.

Expected:

- Notification status is `sent`.
- Approved recipient receives the offer.
- Subject includes quantity and fish type.
- Transaction records `sent`.

SMTP acceptance does not prove the buyer read or accepted the offer.

### MT-142 — SMTP failure isolation

Use an invalid app password in a controlled test and run MT-070.

Expected:

- Notification status becomes `failed`.
- Persistence still runs.
- Final fisher response still appears.
- No false `sent` status is recorded.

Restore dry-run immediately after testing.

## 20. Sample-data tests

### MT-150 — Dataset size

```powershell
(Import-Csv data\market_prices.csv).Count
(Import-Csv data\buyers.csv).Count
```

Expected: 15 markets and 20 buyers.

### MT-151 — Five categories

```powershell
Import-Csv data\market_prices.csv | Select-Object -ExpandProperty fish_type -Unique
```

Expected:

```text
Pomfret
Mackerel
Rohu
Prawns
Tuna
```

### MT-152 — Data variation

Open both CSVs and verify prices, distances, demand, capacities, and freshness
acceptance are not identical across records.

Expected: sufficient variation to change rankings and routes.

## 21. Failure and recovery tests

### MT-160 — Invalid market row

In a backed-up CSV copy, make one matching market price nonnumeric and submit its
fish type.

Expected: Pydantic validation stops retrieval and Streamlit displays a workflow
error. Restore the file. This verifies bad external data is not silently trusted.

### MT-161 — Invalid buyer email

Set one matching buyer email to an invalid value and submit its fish type.

Expected: buyer-record validation fails rather than sending to an invalid
address. Restore the file.

### MT-162 — Empty transaction ledger

Using a safe copy, leave only the CSV header and open Analytics.

Expected:

- All counts and rates are zero.
- Charts without data show informational messages.
- No division-by-zero error occurs.

### MT-163 — Restart behavior

1. Run a successful submission.
2. Stop and restart Streamlit.
3. Open Agent Analysis and Analytics.

Expected:

- In-memory latest-result/checkpoint context is not durable across restart.
- The persisted transaction remains in Analytics.

## 22. Manual regression matrix

Use this compact matrix before submission:

| ID | Feature | Required result |
|---|---|---|
| MT-001 | Startup | Four pages load |
| MT-010 | Valid input | Full graph executes |
| MT-011 | Invalid input | Rejected route persists |
| MT-020/21/22 | Freshness | All three classes observed |
| MT-030/31/33 | Urgency | Low, Medium, High observed |
| MT-040 | Markets | Fish-type-only retrieval |
| MT-041 | Distance | Out-of-radius markets excluded |
| MT-050 | Buyers | Accepted types only |
| MT-051 | Hallucination guard | Rohu returns no buyer |
| MT-060 | Scoring | Five components visible |
| MT-070 | Direct sale | Notification path runs |
| MT-071 | Negotiation | No notification path |
| MT-072 | Fallback | Retrieved market selected |
| MT-090 | Persistence | Row count increases |
| MT-101 | Analytics | Dashboard updates |
| MT-110–115 | Agentic proof | State/tool/route/action evidence visible |
| MT-120 | Gemma 4 Cloud | `gemma4_guardrailed` visible |
| MT-130–133 | Sheets | Seed, retrieve, append |
| MT-140 | Email safety | Dry-run without delivery |
| MT-141 | Live SMTP | Approved recipient receives offer |
| MT-150/151 | Data | 15 markets, 20 buyers, five categories |

## 23. Final agentic acceptance criteria

The project passes the mandatory agentic requirement when a reviewer can observe
all of the following:

- [ ] The application compiles a LangGraph `StateGraph`.
- [ ] State persists across multiple specialized nodes.
- [ ] Retrieval tools execute using current catch context.
- [ ] Buyer scores depend on retrieved records and catch state.
- [ ] The decision is not a fixed response.
- [ ] Three submissions reach three different conditional paths.
- [ ] Only the direct-sale path executes notification.
- [ ] Buyer and market selections come only from retrieved IDs.
- [ ] Gemma 4 structured reasoning is visible when configured.
- [ ] An Ollama/Gemma failure cannot prevent deterministic decision fallback.
- [ ] Actions execute without the user manually selecting a buyer.
- [ ] Every path converges on persistence and a final response.
- [ ] The execution log makes the decision auditable.
- [ ] Analytics reflect persisted outcomes.

The current implementation is designed to satisfy every item. If any item fails
in a configured environment, treat it as a defect; do not describe that run as a
successful agentic demonstration until corrected.

## 24. Test completion report

At the end of testing, summarize:

```text
Offline cases passed / run:
Agentic cases passed / run:
Gemma 4/Ollama cases passed / run / not configured:
Google Sheets cases passed / run / not configured:
Gmail cases passed / run / not configured:
Open critical defects:
Open noncritical defects:
Ledger restored: Yes / No
Approved for demonstration: Yes / No
Tester and date:
```
