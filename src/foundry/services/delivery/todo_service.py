import os
import re
import shutil
from pathlib import Path
from uuid import uuid4

from markupsafe import Markup, escape
from sqlmodel import Session, select

from foundry.models import Todo, TodoComment, TodoDocument, TodoTag, TodoLink

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover - optional dependency fallback
    markdown_lib = None

try:
    import bleach
except ImportError:  # pragma: no cover - optional dependency fallback
    bleach = None


STATIC_ROOT = Path(__file__).resolve().parents[1] / "ui" / "static"
TODO_DOCUMENTS_DIR = STATIC_ROOT / "todo_documents"

MARKDOWN_ALLOWED_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
MARKDOWN_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}


def _render_plaintext_paragraphs(text: str) -> Markup:
    paragraphs: list[str] = []
    for raw_paragraph in re.split(r"\n\s*\n", text):
        escaped = str(escape(raw_paragraph)).replace("\n", "<br>")
        paragraphs.append(f"<p>{escaped}</p>")
    return Markup("".join(paragraphs))


def _sanitize_markdown_html(html: str) -> Markup:
    if bleach is None:
        return Markup(escape(html).replace("\n", "<br>"))

    cleaned = bleach.clean(
        html,
        tags=MARKDOWN_ALLOWED_TAGS,
        attributes=MARKDOWN_ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return Markup(cleaned)


def render_markdown(value: str | None) -> Markup:
    if not value or not value.strip():
        return Markup("")

    text = value.strip()
    if markdown_lib is not None and bleach is not None:
        html = markdown_lib.markdown(text, extensions=["extra", "sane_lists", "nl2br"])
        return _sanitize_markdown_html(html)

    return _render_plaintext_paragraphs(text)


def normalize_tag_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip())
    return normalized[:60]


def make_document_url(storage_path: str | None) -> str | None:
    if not storage_path:
        return None
    normalized = storage_path.replace("\\", "/").strip("/")
    return f"/static/{normalized}" if normalized else None


def store_uploaded_document(upload_file) -> dict:
    original_name = (upload_file.filename or "document").strip() or "document"
    source_path = Path(original_name)
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source_path.stem).strip("-._") or "document"
    safe_suffix = re.sub(r"[^A-Za-z0-9.]+", "", source_path.suffix)[:16]
    filename = f"{uuid4().hex}_{safe_stem[:48]}{safe_suffix}"

    TODO_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = TODO_DOCUMENTS_DIR / filename
    upload_file.file.seek(0)
    with destination.open("wb") as handle:
        shutil.copyfileobj(upload_file.file, handle)

    storage_path = f"todo_documents/{filename}"
    return {
        "title": safe_stem.replace("-", " ").strip() or original_name,
        "storage_path": storage_path,
        "original_filename": original_name,
        "url": make_document_url(storage_path),
    }


def remove_document_file(storage_path: str | None) -> None:
    if not storage_path:
        return
    candidate = STATIC_ROOT / storage_path.replace("/", os.sep)
    try:
        if candidate.is_file():
            candidate.unlink()
    except OSError:
        return


def delete_todo_children(session: Session, todo: Todo) -> list[str]:
    document_rows = list(session.exec(select(TodoDocument).where(TodoDocument.todo_id == todo.id)).all())
    comment_rows = list(session.exec(select(TodoComment).where(TodoComment.todo_id == todo.id)).all())
    tag_rows = list(session.exec(select(TodoTag).where(TodoTag.todo_id == todo.id)).all())
    link_rows = list(session.exec(select(TodoLink).where(TodoLink.todo_id == todo.id)).all())

    storage_paths = [row.storage_path for row in document_rows if row.storage_path]

    for comment_row in comment_rows:
        session.delete(comment_row)
    for tag_row in tag_rows:
        session.delete(tag_row)
    for link_row in link_rows:
        session.delete(link_row)
    for document_row in document_rows:
        session.delete(document_row)

    return storage_paths


def delete_todo_with_children(session: Session, todo: Todo) -> list[str]:
    storage_paths = delete_todo_children(session, todo)
    session.delete(todo)
    session.commit()

    for storage_path in storage_paths:
        remove_document_file(storage_path)

    return storage_paths