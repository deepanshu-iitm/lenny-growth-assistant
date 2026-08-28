from app.essay import topic_query, wants_essay, wants_html


def test_ship30_prompt_is_an_essay():
    text = "Write a Ship 30 essay about how Duolingo grew"
    assert wants_essay(text)
    assert not wants_html(text)
    assert "duolingo" in topic_query(text).lower()


def test_html_one_pager_is_not_an_essay():
    text = "Make an HTML one-pager about how Duolingo grew"
    assert wants_html(text)
    assert not wants_essay(text)
    assert "duolingo" in topic_query(text).lower()


def test_plain_question_is_neither():
    text = "How did Duolingo grow?"
    assert not wants_essay(text)
    assert not wants_html(text)
