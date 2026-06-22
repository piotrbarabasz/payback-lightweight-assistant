# Product Catalog

## 1. Purpose

The Stage 2 synthetic product catalog simulates three PAYBACK partner ecosystems for local development and retrieval testing. It provides realistic product data without depending on production partner feeds, cloud services, embeddings, or vector search.

## 2. Partners

- `dm`: drugstore products such as baby care, cosmetics, personal care, and household items. This partner represents high-frequency, low-price purchases.
- `edeka`: groceries, fresh produce, meal ingredients, beverages, dairy, pantry goods, and organic products.
- `amazon`: general merchandise including electronics, home goods, accessories, sports items, office products, and long-tail items.

## 3. Product Schema

| Field | Type | Notes |
| --- | --- | --- |
| `product_id` | string | Unique product identifier with the partner prefix, for example `dm-001`. |
| `partner` | enum | One of `dm`, `edeka`, or `amazon`. |
| `name` | string | English product name. |
| `name_de` | string | German product name. |
| `category` | string | Product category used for filtering and future retrieval. |
| `description` | string | English product description. |
| `description_de` | string | German product description. |
| `brand` | string | Product brand or synthetic private-label brand. |
| `price` | float | Non-negative product price. |
| `currency` | string | Currency code, default `EUR`. |
| `tags` | list[string] | English retrieval and filtering tags. |
| `tags_de` | list[string] | German retrieval and filtering tags. |
| `availability` | boolean | Whether the product is currently available, default `true`. |
| `popularity_score` | float | Synthetic popularity signal from `0` to `1`, default `0.5`. |
| `is_promotion` | boolean | Whether the product is currently promoted, default `false`. |
| `product_url` | string or null | Optional product detail URL. |

## 4. Dataset Size

Target catalog size:

- 50 products for `dm`
- 50 products for `edeka`
- 50 products for `amazon`
- 150 products total

## 5. Data Quality Rules

- `product_id` must be unique.
- `partner` must be one of `dm`, `edeka`, or `amazon`.
- `price` must be non-negative.
- `tags` and `tags_de` should not be empty.
- German fields `name_de` and `description_de` should be present.
- Each partner should include products from multiple categories.

## 6. Future Use

The catalog is designed to support later stages, including:

- keyword search (implemented in Stage 3)
- vector search
- hybrid retrieval
- ranking
- BigQuery import
- embeddings generation
