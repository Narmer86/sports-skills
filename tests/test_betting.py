"""Tests for betting analysis calculations."""

from sports_skills.betting._calcs import (
    convert_odds,
    devig,
    evaluate_bet,
    find_edge,
    kelly_criterion,
    max_drawdown,
    monte_carlo_sim,
)

# ============================================================
# Convert Odds
# ============================================================


class TestConvertOdds:
    def test_american_negative(self):
        # -150 → prob = 150/250 = 0.6
        result = convert_odds({"params": {"odds": -150, "from_format": "american"}})
        assert result["status"] is True
        assert abs(result["data"]["implied_probability"] - 0.6) < 0.001

    def test_american_positive(self):
        # +130 → prob = 100/230 ≈ 0.4348
        result = convert_odds({"params": {"odds": 130, "from_format": "american"}})
        assert result["status"] is True
        assert abs(result["data"]["implied_probability"] - 0.4348) < 0.001

    def test_american_even(self):
        # +100 → prob = 100/200 = 0.5
        result = convert_odds({"params": {"odds": 100, "from_format": "american"}})
        assert result["status"] is True
        assert abs(result["data"]["implied_probability"] - 0.5) < 0.001

    def test_american_heavy_favorite(self):
        # -500 → prob = 500/600 ≈ 0.8333
        result = convert_odds({"params": {"odds": -500, "from_format": "american"}})
        assert result["status"] is True
        assert abs(result["data"]["implied_probability"] - 0.8333) < 0.001

    def test_decimal(self):
        # 2.50 → prob = 1/2.5 = 0.4
        result = convert_odds({"params": {"odds": 2.50, "from_format": "decimal"}})
        assert result["status"] is True
        assert abs(result["data"]["implied_probability"] - 0.4) < 0.001

    def test_decimal_invalid(self):
        result = convert_odds({"params": {"odds": 0.5, "from_format": "decimal"}})
        assert result["status"] is False

    def test_probability(self):
        # 0.6 → american = -150, decimal = 1.6667
        result = convert_odds({"params": {"odds": 0.6, "from_format": "probability"}})
        assert result["status"] is True
        assert abs(result["data"]["american"] - (-150.0)) < 0.1
        assert abs(result["data"]["decimal"] - 1.6667) < 0.001

    def test_probability_invalid(self):
        result = convert_odds({"params": {"odds": 1.5, "from_format": "probability"}})
        assert result["status"] is False

    def test_unknown_format(self):
        result = convert_odds({"params": {"odds": 100, "from_format": "fractional"}})
        assert result["status"] is False

    def test_roundtrip_american(self):
        # Convert american → prob → american should be consistent
        r1 = convert_odds({"params": {"odds": -200, "from_format": "american"}})
        prob = r1["data"]["implied_probability"]
        r2 = convert_odds({"params": {"odds": prob, "from_format": "probability"}})
        assert abs(r2["data"]["american"] - (-200.0)) < 0.5


# ============================================================
# De-vig
# ============================================================


class TestDevig:
    def test_standard_spread(self):
        # -110/-110 → each side ~52.38% → fair 50%/50%
        result = devig({"params": {"odds": "-110,-110", "format": "american"}})
        assert result["status"] is True
        outcomes = result["data"]["outcomes"]
        assert len(outcomes) == 2
        assert abs(outcomes[0]["fair_prob"] - 0.5) < 0.001
        assert abs(outcomes[1]["fair_prob"] - 0.5) < 0.001
        assert result["data"]["vig_pct"] > 0

    def test_two_way_market(self):
        # -150/+130 → probs sum > 1, de-vig removes overround
        result = devig({"params": {"odds": "-150,+130", "format": "american"}})
        assert result["status"] is True
        outcomes = result["data"]["outcomes"]
        total_fair = sum(o["fair_prob"] for o in outcomes)
        assert abs(total_fair - 1.0) < 0.001

    def test_three_way_soccer(self):
        # Soccer 3-way moneyline
        result = devig({"params": {"odds": "-120,+250,+350", "format": "american"}})
        assert result["status"] is True
        outcomes = result["data"]["outcomes"]
        assert len(outcomes) == 3
        total_fair = sum(o["fair_prob"] for o in outcomes)
        assert abs(total_fair - 1.0) < 0.001

    def test_decimal_format(self):
        result = devig({"params": {"odds": "1.91,1.91", "format": "decimal"}})
        assert result["status"] is True
        outcomes = result["data"]["outcomes"]
        assert abs(outcomes[0]["fair_prob"] - 0.5) < 0.01

    def test_probability_format(self):
        result = devig({"params": {"odds": "0.55,0.50", "format": "probability"}})
        assert result["status"] is True
        total_fair = sum(o["fair_prob"] for o in result["data"]["outcomes"])
        assert abs(total_fair - 1.0) < 0.001

    def test_list_input(self):
        result = devig({"params": {"odds": [-150, 130], "format": "american"}})
        assert result["status"] is True

    def test_single_outcome_error(self):
        result = devig({"params": {"odds": "-150", "format": "american"}})
        assert result["status"] is False

    def test_missing_odds(self):
        result = devig({"params": {}})
        assert result["status"] is False

    def test_overround_positive(self):
        # Any real book odds should have positive vig
        result = devig({"params": {"odds": "-110,-110", "format": "american"}})
        assert result["data"]["overround"] > 1.0
        assert result["data"]["vig_pct"] > 0


# ============================================================
# Find Edge
# ============================================================


class TestFindEdge:
    def test_positive_edge(self):
        result = find_edge({"params": {"fair_prob": 0.60, "market_prob": 0.50}})
        assert result["status"] is True
        assert result["data"]["edge"] > 0
        assert result["data"]["ev_per_dollar"] > 0
        assert result["data"]["recommendation"] == "bet"

    def test_negative_edge(self):
        result = find_edge({"params": {"fair_prob": 0.40, "market_prob": 0.50}})
        assert result["status"] is True
        assert result["data"]["edge"] < 0
        assert result["data"]["ev_per_dollar"] < 0
        assert result["data"]["recommendation"] == "no bet"

    def test_zero_edge(self):
        result = find_edge({"params": {"fair_prob": 0.50, "market_prob": 0.50}})
        assert result["status"] is True
        assert result["data"]["edge"] == 0
        assert result["data"]["recommendation"] == "no bet"

    def test_known_values(self):
        # fair=0.60, market=0.50 → edge=0.10, EV=0.20, Kelly=0.20
        result = find_edge({"params": {"fair_prob": 0.60, "market_prob": 0.50}})
        assert abs(result["data"]["edge"] - 0.10) < 0.001
        assert abs(result["data"]["ev_per_dollar"] - 0.20) < 0.001
        assert abs(result["data"]["kelly_fraction"] - 0.20) < 0.001

    def test_invalid_fair_prob(self):
        result = find_edge({"params": {"fair_prob": 1.5, "market_prob": 0.50}})
        assert result["status"] is False

    def test_invalid_market_prob(self):
        result = find_edge({"params": {"fair_prob": 0.50, "market_prob": 0}})
        assert result["status"] is False


# ============================================================
# Kelly Criterion
# ============================================================


class TestKellyCriterion:
    def test_positive_edge(self):
        result = kelly_criterion({"params": {"fair_prob": 0.60, "market_prob": 0.50}})
        assert result["status"] is True
        assert result["data"]["kelly_fraction"] > 0
        assert result["data"]["recommendation"] == "bet"

    def test_negative_edge(self):
        result = kelly_criterion({"params": {"fair_prob": 0.40, "market_prob": 0.50}})
        assert result["status"] is True
        assert result["data"]["kelly_fraction"] < 0
        assert result["data"]["recommendation"] == "no bet"

    def test_known_kelly(self):
        # fair=0.60, market=0.50 → f* = (0.60-0.50)/(1-0.50) = 0.20
        result = kelly_criterion({"params": {"fair_prob": 0.60, "market_prob": 0.50}})
        assert abs(result["data"]["kelly_fraction"] - 0.20) < 0.001

    def test_small_edge(self):
        # fair=0.52, market=0.50 → f* = 0.02/0.50 = 0.04
        result = kelly_criterion({"params": {"fair_prob": 0.52, "market_prob": 0.50}})
        assert abs(result["data"]["kelly_fraction"] - 0.04) < 0.001

    def test_net_odds_computed(self):
        # market=0.40 → b = 1/0.40 - 1 = 1.5
        result = kelly_criterion({"params": {"fair_prob": 0.60, "market_prob": 0.40}})
        assert abs(result["data"]["net_odds"] - 1.5) < 0.001

    def test_invalid_fair_prob(self):
        result = kelly_criterion({"params": {"fair_prob": 0, "market_prob": 0.50}})
        assert result["status"] is False

    def test_invalid_market_prob(self):
        result = kelly_criterion({"params": {"fair_prob": 0.50, "market_prob": 1.0}})
        assert result["status"] is False


# ============================================================
# Monte Carlo Simulation
# ============================================================


class TestMonteCarloSim:
    def test_basic_simulation(self):
        result = monte_carlo_sim({
            "params": {
                "returns": "0.08,-0.04,0.06,-0.03,0.07",
                "n_simulations": 100,
                "seed": 42,
            }
        })
        assert result["status"] is True
        assert result["data"]["simulations"] == 100
        assert "final_value" in result["data"]
        assert "max_drawdown" in result["data"]
        assert "probability_of_profit" in result["data"]

    def test_deterministic_with_seed(self):
        params = {
            "returns": "0.05,-0.02,0.03",
            "n_simulations": 50,
            "seed": 123,
        }
        r1 = monte_carlo_sim({"params": params})
        r2 = monte_carlo_sim({"params": params})
        assert r1["data"]["final_value"]["mean"] == r2["data"]["final_value"]["mean"]

    def test_custom_bankroll(self):
        result = monte_carlo_sim({
            "params": {
                "returns": "0.05,-0.02",
                "n_simulations": 10,
                "initial_bankroll": 5000,
                "seed": 1,
            }
        })
        assert result["data"]["initial_bankroll"] == 5000

    def test_sample_paths_included(self):
        result = monte_carlo_sim({
            "params": {
                "returns": "0.05,-0.02,0.03",
                "n_simulations": 30,
                "seed": 42,
            }
        })
        assert len(result["data"]["sample_paths"]) == 20  # capped at 20

    def test_missing_returns(self):
        result = monte_carlo_sim({"params": {}})
        assert result["status"] is False

    def test_single_return_error(self):
        result = monte_carlo_sim({"params": {"returns": "0.05"}})
        assert result["status"] is False

    def test_list_returns(self):
        result = monte_carlo_sim({
            "params": {
                "returns": [0.05, -0.02, 0.03],
                "n_simulations": 10,
                "seed": 42,
            }
        })
        assert result["status"] is True

    def test_all_positive_returns_high_profit_prob(self):
        result = monte_carlo_sim({
            "params": {
                "returns": "0.05,0.03,0.08,0.02,0.04",
                "n_simulations": 1000,
                "seed": 42,
            }
        })
        assert result["data"]["probability_of_profit"] > 0.9

    def test_excessive_simulations_rejected(self):
        result = monte_carlo_sim({
            "params": {"returns": "0.05,-0.02", "n_simulations": 200000}
        })
        assert result["status"] is False


# ============================================================
# Maximum Drawdown
# ============================================================


class TestMaxDrawdown:
    def test_no_drawdown(self):
        result = max_drawdown({"params": {"values": "100,110,120,130"}})
        assert result["status"] is True
        assert result["data"]["max_drawdown"] == 0.0

    def test_known_drawdown(self):
        # 100 -> 120 -> 90: drawdown = (90-120)/120 = -0.25
        result = max_drawdown({"params": {"values": "100,120,90"}})
        assert result["status"] is True
        assert abs(result["data"]["max_drawdown"] - (-0.25)) < 0.001

    def test_recovery_after_drawdown(self):
        result = max_drawdown({"params": {"values": "100,120,90,150"}})
        assert result["status"] is True
        assert abs(result["data"]["max_drawdown"] - (-0.25)) < 0.001

    def test_peak_and_trough_indices(self):
        result = max_drawdown({"params": {"values": "100,120,90,150"}})
        assert result["data"]["peak_index"] == 1  # 120
        assert result["data"]["trough_index"] == 2  # 90

    def test_drawdown_series_length(self):
        result = max_drawdown({"params": {"values": "100,110,105,115,108"}})
        assert len(result["data"]["drawdown_series"]) == 5

    def test_missing_values(self):
        result = max_drawdown({"params": {}})
        assert result["status"] is False

    def test_single_value(self):
        result = max_drawdown({"params": {"values": "100"}})
        assert result["status"] is False

    def test_list_input(self):
        result = max_drawdown({"params": {"values": [100, 120, 90]}})
        assert result["status"] is True
        assert abs(result["data"]["max_drawdown"] - (-0.25)) < 0.001


# ============================================================
# Evaluate Bet (all-in-one)
# ============================================================


class TestEvaluateBet:
    def test_basic_evaluation(self):
        result = evaluate_bet({
            "params": {
                "book_odds": "-150,+130",
                "market_prob": 0.52,
            }
        })
        assert result["status"] is True
        assert "devig" in result["data"]
        assert "edge" in result["data"]
        assert "recommendation" in result["data"]
        assert "summary" in result["data"]

    def test_with_monte_carlo(self):
        result = evaluate_bet({
            "params": {
                "book_odds": "-150,+130",
                "market_prob": 0.52,
                "returns": "0.08,-0.04,0.06,-0.03,0.07",
                "n_simulations": 100,
                "seed": 42,
            }
        })
        assert result["status"] is True
        assert "monte_carlo" in result["data"]

    def test_no_edge_no_bet(self):
        # If market prob matches fair prob, should be no bet
        # -110/-110 → fair 50%/50%, market at 0.50 → no edge
        result = evaluate_bet({
            "params": {
                "book_odds": "-110,-110",
                "market_prob": 0.50,
            }
        })
        assert result["status"] is True
        assert abs(result["data"]["edge"]["edge"]) < 0.01

    def test_decimal_format(self):
        result = evaluate_bet({
            "params": {
                "book_odds": "1.67,2.30",
                "book_format": "decimal",
                "market_prob": 0.52,
            }
        })
        assert result["status"] is True

    def test_second_outcome(self):
        # Evaluate the second outcome (away team / underdog)
        result = evaluate_bet({
            "params": {
                "book_odds": "-150,+130",
                "market_prob": 0.52,
                "outcome": 1,
            }
        })
        assert result["status"] is True
        # The away side fair prob should be ~42%
        fair_prob = result["data"]["devig"]["outcomes"][1]["fair_prob"]
        assert 0.35 < fair_prob < 0.50

    def test_missing_book_odds(self):
        result = evaluate_bet({"params": {"market_prob": 0.50}})
        assert result["status"] is False

    def test_invalid_market_prob(self):
        result = evaluate_bet({
            "params": {"book_odds": "-150,+130", "market_prob": 1.5}
        })
        assert result["status"] is False

    def test_outcome_out_of_range(self):
        result = evaluate_bet({
            "params": {
                "book_odds": "-150,+130",
                "market_prob": 0.50,
                "outcome": 5,
            }
        })
        assert result["status"] is False
