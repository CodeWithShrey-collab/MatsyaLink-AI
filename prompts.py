"""Prompts and deterministic templates used by the reasoning nodes."""

SYSTEM_PROMPT = """
You are MatsyaLink AI, an autonomous market-access agent supporting SDG 14.b.

Operating rules:
1. Use the supplied retrieval and scoring tool outputs; base every buyer and
   market statement only on those records.
2. Never invent, rename, merge, or infer a buyer or market.
3. Return output matching the supplied schema exactly.
4. Respect the scoring evidence and the fisher's minimum price.
5. A direct sale is allowed only when the selected buyer's offered price meets
   the fisher's expected minimum price.
6. Use negotiation when buyers exist but no acceptable offer meets the minimum.
7. Use alternate_market when no eligible buyer exists.
8. Explain the decision with price, distance, demand, capacity, freshness, and
   expected-revenue evidence. Do not reveal private chain-of-thought; provide a
   concise, auditable decision rationale.
""".strip()


DECISION_PROMPT = """
Evaluate this already retrieved and scored marketplace evidence.

Catch:
{catch_json}

Freshness: {freshness}
Urgency: {urgency}
Eligible markets:
{markets_json}

Eligible buyers:
{buyers_json}

Weighted buyer scores (highest first):
{scores_json}

Policy-determined allowed decision: {allowed_decision}
Policy-preferred buyer id: {preferred_buyer_id}
Policy-preferred market id: {preferred_market_id}

Return a transparent decision. The decision must equal the allowed decision.
Any selected id must be copied exactly from the eligible evidence. For a
negotiation, give a short practical strategy for the fisher.
""".strip()


EMAIL_SUBJECT_TEMPLATE = "MatsyaLink catch offer: {quantity:.1f} kg {fish_type}"


EMAIL_BODY_TEMPLATE = """Dear {buyer_name},

MatsyaLink AI has matched your current demand with a fresh catch offer.

Fish type: {fish_type}
Quantity available: {quantity:.1f} kg
Fisher location: {location}
Expected minimum price: INR {expected_price:.2f}/kg
Your listed offer: INR {offered_price:.2f}/kg
Catch freshness: {freshness}
Estimated order value: INR {revenue:,.2f}

Please reply to confirm availability and collection arrangements. This offer is
generated from the fisher's submitted details and your stored demand record.

Regards,
MatsyaLink AI
""".strip()
