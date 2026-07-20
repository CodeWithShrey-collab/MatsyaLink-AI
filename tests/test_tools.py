from tools import generate_analytics, get_available_buyers, get_market_prices


def test_market_tool_only_returns_requested_fish_type():
    records = get_market_prices.invoke({"fish_type": "Rohu"})
    assert len(records) == 3
    assert {record["fish_type"] for record in records} == {"Rohu"}


def test_buyer_tool_never_invents_unavailable_category():
    assert get_available_buyers.invoke({"fish_type": "Rohu"}) == []


def test_analytics_shape():
    result = generate_analytics.invoke({})
    expected = {
        "total_catches_processed",
        "average_revenue",
        "success_rate",
        "negotiation_rate",
        "no_buyer_rate",
        "fish_type_counts",
        "buyer_utilization",
        "market_utilization",
    }
    assert expected.issubset(result)

