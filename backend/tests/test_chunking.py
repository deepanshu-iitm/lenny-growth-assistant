from app.chunking import chunk_markdown


def test_chunks_follow_headings():
    text = """# Title

intro words here that count toward the first section.

## Later

more words under the second heading.
"""
    chunks = chunk_markdown(text, target_words=50, overlap_words=0)
    headings = [c["heading"] for c in chunks]
    assert "Title" in headings
    assert "Later" in headings
    assert all(c["token_count"] >= 1 for c in chunks)
