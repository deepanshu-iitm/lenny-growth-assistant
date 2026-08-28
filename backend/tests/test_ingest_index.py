from app.ingest import _index_rows, _parse_date


def test_starter_pack_index_shape():
    data = {
        "podcasts": [
            {"title": "Jen Abel", "filename": "podcasts/jen-abel.md", "guest": "Jen Abel"}
        ],
        "newsletters": [
            {
                "title": "How Duolingo reignited user growth",
                "filename": "newsletters/duolingo.md",
                "date": "2023-02-28",
            }
        ],
    }
    rows = _index_rows(data)
    by_path = {row["path"]: row for row in rows}
    assert by_path["podcasts/jen-abel.md"]["source_type"] == "podcast"
    assert by_path["newsletters/duolingo.md"]["source_type"] == "newsletter"
    assert _parse_date("2023-02-28").isoformat() == "2023-02-28"


def test_sample_index_is_a_list():
    rows = _index_rows(
        [{"path": "podcasts/retention.md", "title": "How to think about retention"}]
    )
    assert rows[0]["path"] == "podcasts/retention.md"
