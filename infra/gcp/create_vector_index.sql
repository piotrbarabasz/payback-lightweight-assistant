-- Optional Stage 8C BigQuery vector index setup.
--
-- This template is not required for the tiny local/synthetic catalog. BigQuery
-- VECTOR_SEARCH can run without a vector index by using brute-force search.
-- For larger production catalogs, a vector index can reduce query latency and
-- scanned work, at the cost of index build/maintenance/storage overhead.
--
-- BigQuery manages vector indexes asynchronously. After this statement
-- completes, the index can still take time to populate. VECTOR_SEARCH can still
-- work during that window, but may be slower until index coverage improves.
--
-- Replace project, dataset, table, and index names before running manually, or
-- use scripts/gcp/create_bigquery_vector_index.py to render and execute the SQL.

CREATE VECTOR INDEX IF NOT EXISTS products_embedding_idx
ON `your-project.payback_catalog.products`(embedding)
STORING (product_id, partner, name, category, price, currency, availability)
OPTIONS (
  index_type = 'IVF',
  distance_type = 'COSINE'
);
