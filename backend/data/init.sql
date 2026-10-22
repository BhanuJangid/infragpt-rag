CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS runbook_chunks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(64)
);

CREATE INDEX IF NOT EXISTS runbook_chunks_embedding_idx
    ON runbook_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);
