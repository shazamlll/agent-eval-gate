"""Tests for the deterministic rubric judge."""

from eval_gate import judge


def test_normalize_strips_accents_and_punctuation():
    assert judge.normalize("Tomás Rivera!") == "tomas rivera"
    assert judge.normalize("  $18.99  ") == "$18.99"


def test_fact_present_number_whole_word():
    # Gold fact "2" must not match the "2" inside "2022" or "$24.50".
    assert judge.fact_present("2", "There are 2 books.") is True
    assert judge.fact_present("2", "Published in 2022.") is False
    assert judge.fact_present("$24.50", "It costs $24.50.") is True
    assert judge.fact_present("$24.50", "It costs $24.00.") is False


def test_groundedness_all_half_none():
    assert judge.score_groundedness(["apple", "berry"], "apple and berry") == 2
    assert judge.score_groundedness(["apple", "berry"], "only apple here") == 1
    assert judge.score_groundedness(["apple", "berry"], "nothing matches") == 0
    assert judge.score_groundedness([], "anything") == 2


def test_relevance_overlap_bands():
    # Content words of this question: fantasy, ada, marsh, catalog (4).
    q = "Which fantasy books by Ada Marsh are in the catalog?"
    assert judge.score_relevance(q, "Fantasy books by Ada Marsh.") == 2
    assert judge.score_relevance(q, "Ada wrote something.") == 1  # 1/4 overlap
    assert judge.score_relevance(q, "The weather is nice today.") == 0


def test_accuracy_distractor_is_critical():
    score, matched = judge.score_accuracy(["is in stock"],
                                          "It is in stock today.")
    assert score == 0 and matched == ["is in stock"]
    score, matched = judge.score_accuracy(["is in stock"],
                                          "It is out of stock today.")
    assert score == 2 and matched == []


def test_accuracy_empty_answer_is_zero():
    score, _ = judge.score_accuracy([], "")
    assert score == 0


def test_accuracy_no_wrong_fact_is_two():
    # "No idea." states no wrong fact -- it fails on groundedness and
    # relevance instead. Accuracy only measures false statements.
    score, _ = judge.score_accuracy([], "No idea.")
    assert score == 2


def test_score_case_pass_and_critical():
    case = {"id": "T1", "question": "Who wrote 'Salt & Cinder'?",
            "gold_facts": ["Ada Marsh"], "distractors": ["Mei Lin"]}
    good = judge.score_case(case, "Ada Marsh wrote 'Salt & Cinder'.")
    assert good["passed"] is True and good["critical"] is False
    assert good["total"] >= 4

    bad = judge.score_case(case, "Mei Lin wrote 'Salt & Cinder'.")
    assert bad["passed"] is False and bad["critical"] is True
    assert bad["accuracy"] == 0


def test_score_case_empty_answer_fails():
    case = {"id": "T2", "question": "Who wrote 'Salt & Cinder'?",
            "gold_facts": ["Ada Marsh"], "distractors": []}
    result = judge.score_case(case, "")
    assert result["passed"] is False
    assert result["total"] == 0
