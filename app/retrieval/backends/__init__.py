"""Optional managed retrieval backends."""

from app.retrieval.backends.bigquery_vector import BigQueryVectorProductRetriever

__all__ = ["BigQueryVectorProductRetriever"]
