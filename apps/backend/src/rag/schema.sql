-- ==============================================================================
-- Supabase pgvector Schema for Spec-to-Playwright RAG Knowledge Base
-- Model: BAAI/bge-small-en-v1.5 (384 dimensions)
-- ==============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the test_knowledge_base table
CREATE TABLE IF NOT EXISTS test_knowledge_base (
    id BIGSERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    chunk_type TEXT NOT NULL, -- 'page_object', 'utility', 'spec_pattern'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create HNSW index for high-performance cosine similarity vector search
CREATE INDEX IF NOT EXISTS test_knowledge_base_embedding_hnsw_idx 
ON test_knowledge_base 
USING hnsw (embedding vector_cosine_ops);

-- 4. Create index on chunk_type and file_path for filtered hybrid queries
CREATE INDEX IF NOT EXISTS test_knowledge_base_chunk_type_idx 
ON test_knowledge_base (chunk_type);

CREATE INDEX IF NOT EXISTS test_knowledge_base_file_path_idx 
ON test_knowledge_base (file_path);

-- 5. RPC function: match_test_chunks
-- Executes cosine similarity search returning the top matching Playwright code chunks
CREATE OR REPLACE FUNCTION match_test_chunks (
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.2,
    match_count INT DEFAULT 5,
    filter_chunk_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    file_path TEXT,
    chunk_type TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tkb.id,
        tkb.file_path,
        tkb.chunk_type,
        tkb.content,
        tkb.metadata,
        1 - (tkb.embedding <=> query_embedding) AS similarity
    FROM test_knowledge_base tkb
    WHERE (filter_chunk_type IS NULL OR tkb.chunk_type = filter_chunk_type)
      AND (1 - (tkb.embedding <=> query_embedding)) >= match_threshold
    ORDER BY tkb.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;

