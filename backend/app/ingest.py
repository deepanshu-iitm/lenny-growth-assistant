import hashlib
import json
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunking import chunk_markdown
from app.config import settings
from app.models import Chunk, Source


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _title_from_markdown(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("-", " ").title()


def _source_type(relative: Path) -> str:
    parts = {p.lower() for p in relative.parts}
    if "newsletter" in parts or "newsletters" in parts:
        return "newsletter"
    return "podcast"


def _load_index(root: Path) -> dict:
    index_path = root / "index.json"
    if not index_path.exists():
        return {}
    data = json.loads(index_path.read_text(encoding="utf-8"))
    by_path = {}
    for row in data:
        rel = row.get("path")
        if rel:
            by_path[rel.replace("\\", "/")] = row
    return by_path


async def _replace_chunks(db: AsyncSession, source: Source) -> int:
    await db.execute(delete(Chunk).where(Chunk.source_id == source.id))
    pieces = chunk_markdown(source.content)
    for i, piece in enumerate(pieces):
        db.add(
            Chunk(
                source_id=source.id,
                ordinal=i,
                heading=piece["heading"],
                content=piece["content"],
                token_count=piece["token_count"],
            )
        )
    return len(pieces)


async def ingest_sources(db: AsyncSession) -> dict:
    root = Path(settings.data_dir)
    if not root.exists():
        return {"error": f"data_dir not found: {root}", "ingested": 0, "updated": 0, "skipped": 0}

    index = _load_index(root)
    ingested = updated = skipped = 0
    chunks_written = 0

    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        checksum = _checksum(text)
        meta = index.get(relative, {})

        existing = await db.scalar(select(Source).where(Source.path == relative))
        if existing and existing.checksum == checksum:
            chunk_count = await db.scalar(
                select(func.count()).select_from(Chunk).where(Chunk.source_id == existing.id)
            )
            if chunk_count:
                skipped += 1
                continue
            await db.flush()
            chunks_written += await _replace_chunks(db, existing)
            updated += 1
            continue

        title = meta.get("title") or _title_from_markdown(path, text)
        guest = meta.get("guest")
        source_type = meta.get("source_type") or _source_type(path.relative_to(root))

        if existing:
            existing.title = title
            existing.guest = guest
            existing.source_type = source_type
            existing.checksum = checksum
            existing.content = text
            source = existing
            updated += 1
        else:
            source = Source(
                source_type=source_type,
                title=title,
                guest=guest,
                path=relative,
                checksum=checksum,
                content=text,
            )
            db.add(source)
            ingested += 1

        await db.flush()
        chunks_written += await _replace_chunks(db, source)

    await db.commit()
    return {
        "ingested": ingested,
        "updated": updated,
        "skipped": skipped,
        "chunks": chunks_written,
        "data_dir": str(root),
    }
