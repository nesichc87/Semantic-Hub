from app.sources.ranking import rank_matches


def test_rank_matches_orders_exact_before_prefix_before_substring():
    candidates = {
        "x:a": ["Millimetre"],
        "x:b": ["Metre per Second"],
        "x:c": ["Metre"],
    }

    assert rank_matches("metre", candidates) == ["x:c", "x:b", "x:a"]


def test_rank_matches_excludes_candidates_without_match():
    candidates = {
        "x:a": ["Metre"],
        "x:b": ["Foot"],
    }

    assert rank_matches("metre", candidates) == ["x:a"]


def test_rank_matches_uses_best_matching_text_of_a_candidate():
    candidates = {
        "x:a": ["Metre per Second"],
        "x:b": ["MilliM", "Metre"],
    }

    assert rank_matches("metre", candidates) == ["x:b", "x:a"]


def test_rank_matches_sorts_alphabetically_within_the_same_rank():
    candidates = {
        "x:b": ["Millimetre"],
        "x:a": ["Centimetre"],
    }

    assert rank_matches("metre", candidates) == ["x:a", "x:b"]


def test_rank_matches_is_case_insensitive_and_ignores_surrounding_whitespace():
    candidates = {"x:a": ["Metre"]}

    assert rank_matches("  METRE  ", candidates) == ["x:a"]


def test_rank_matches_returns_empty_list_for_blank_query():
    candidates = {"x:a": ["Metre"]}

    assert rank_matches("   ", candidates) == []