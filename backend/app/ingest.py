import hashlib
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Source


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


async def ingest_sources(db: AsyncSession) -> dict:
    root = Path(settings.data_dir)
    if not root.exists():
        return {"error": f"data_dir not found: {root}", "ingested": 0, "updated": 0, "skipped": 0}

    index = _load_index(root)
    ingested = updated = skipped = 0

    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        checksum = _checksum(text)
        meta = index.get(relative, {})

        existing = await db.scalar(select(Source).where(Source.path == relative))
        if existing and existing.checksum == checksum:
            skipped += 1
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
            updated += 1
        else:
            db.add(
                Source(
                    source_type=source_type,
                    title=title,
                    guest=guest,
                    path=relative,
                    checksum=checksum,
                    content=text,
                )
            )
            ingested += 1

    await db.commit()
    return {"ingested": ingested, "updated": updated, "skipped": skipped, "data_dir": str(root)}
