from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.schemas import Source

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # demo still runs without LangChain installed
    RecursiveCharacterTextSplitter = None


TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def _split_text(text: str, chunk_size: int = 700, overlap: int = 80) -> list[str]:
    if RecursiveCharacterTextSplitter is not None:
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=overlap
        ).split_text(text)
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


@dataclass
class Chunk:
    title: str
    path: str
    text: str
    tf: dict[str, float]
    norm: float


class RunbookIndex:
    """Lexical TF-IDF index over markdown runbooks.

    Works offline without an embedding API. When OPENAI_API_KEY is set, the
    chat layer still uses an LLM; retrieval stays local and deterministic.
    """

    def __init__(self, runbook_dir: Path | None = None) -> None:
        self.runbook_dir = runbook_dir or (settings.data_dir / "runbooks")
        self.chunks: list[Chunk] = []
        self.df: dict[str, int] = {}
        self._build()

    @property
    def size(self) -> int:
        return len(self.chunks)

    def _build(self) -> None:
        files = sorted(self.runbook_dir.glob("*.md"))
        raw: list[tuple[str, str, str]] = []
        for path in files:
            text = path.read_text(encoding="utf-8").strip()
            title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
            rel = str(path.relative_to(settings.data_dir))
            for chunk in _split_text(text):
                raw.append((title, rel, chunk))

        df: dict[str, int] = {}
        tokenized: list[list[str]] = []
        for _, _, text in raw:
            tokens = _tokenize(text)
            tokenized.append(tokens)
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        self.df = df
        n = max(len(raw), 1)

        for (title, rel, text), tokens in zip(raw, tokenized):
            tf: dict[str, float] = {}
            for term in tokens:
                tf[term] = tf.get(term, 0.0) + 1.0
            weighted: dict[str, float] = {}
            acc = 0.0
            for term, count in tf.items():
                idf = math.log((n + 1) / (df[term] + 1)) + 1.0
                w = (count / max(len(tokens), 1)) * idf
                weighted[term] = w
                acc += w * w
            self.chunks.append(Chunk(title, rel, text, weighted, math.sqrt(acc) or 1.0))

    def search(self, query: str, k: int = 4) -> list[Source]:
        q_tokens = _tokenize(query)
        if not q_tokens or not self.chunks:
            return []
        q_tf: dict[str, float] = {}
        for term in q_tokens:
            q_tf[term] = q_tf.get(term, 0.0) + 1.0
        n = max(len(self.chunks), 1)
        q_w: dict[str, float] = {}
        q_acc = 0.0
        for term, count in q_tf.items():
            idf = math.log((n + 1) / (self.df.get(term, 0) + 1)) + 1.0
            w = (count / len(q_tokens)) * idf
            q_w[term] = w
            q_acc += w * w
        q_norm = math.sqrt(q_acc) or 1.0

        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            dot = 0.0
            for term, w in q_w.items():
                dot += w * chunk.tf.get(term, 0.0)
            score = dot / (chunk.norm * q_norm)
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        sources: list[Source] = []
        for score, chunk in scored[:k]:
            if score <= 0:
                continue
            snippet = " ".join(chunk.text.split())[:280]
            sources.append(
                Source(title=chunk.title, path=chunk.path, score=round(score, 4), snippet=snippet)
            )
        return sources

    def context_block(self, sources: list[Source]) -> str:
        if not sources:
            return "No matching runbook chunks."
        by_path = {c.path: c.text for c in self.chunks}
        parts = []
        for src in sources:
            parts.append(f"### {src.title} ({src.path})\n{by_path.get(src.path, src.snippet)}")
        return "\n\n".join(parts)


index = RunbookIndex()
