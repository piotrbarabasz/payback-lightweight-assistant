"""Vector similarity helpers for embedding experiments."""

from __future__ import annotations

import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for two vectors, or 0.0 for invalid inputs."""

    if not left or not right or len(left) != len(right):
        return 0.0

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)
