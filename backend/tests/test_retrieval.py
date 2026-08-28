from types import SimpleNamespace

from app.retrieval import _score, answer_from_hits, query_terms


def test_query_drops_tiny_words():
    assert "how" not in query_terms("How did Duolingo grow?")
    assert "duolingo" in query_terms("How did Duolingo grow?")


def test_title_beats_body_for_duolingo():
    terms = query_terms("how did duolingo grow")
    named = SimpleNamespace(
        source=SimpleNamespace(
            title="How Duolingo reignited user growth",
            guest=None,
            content="",
        ),
        content="unrelated body",
    )
    generic = SimpleNamespace(
        source=SimpleNamespace(title="Hiring at Cursor", guest="Adam Ward"),
        content="Companies grow when they hire. Grow grow grow.",
    )
    assert _score(named, terms) > _score(generic, terms)


def test_empty_hits_do_not_invent():
    text, citations = answer_from_hits([])
    assert citations == []
    assert "doesn't support" in text


def test_citations_dedupe_by_path():
    source = SimpleNamespace(
        title="How Duolingo reignited user growth",
        guest=None,
        path="newsletters/duolingo.md",
        source_type="newsletter",
    )
    a = SimpleNamespace(source=source, heading="One", content="first")
    b = SimpleNamespace(source=source, heading="Two", content="second")
    _, citations = answer_from_hits([a, b])
    assert len(citations) == 1
