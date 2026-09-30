# Data dictionary

| Field | Type | Required | Meaning |
|---|---|---|---|
| date | Calendar date | Yes | Sales date, normalized to a day |
| sales | Finite numeric | Yes | Net sales revenue in one currency |
| product | Text | No | Product name/identifier |
| category | Text | No | Product grouping |
| store | Text | No | Store/channel |
| region | Text | No | Geographic grouping |
| quantity | Numeric | No | Units sold; unknown values excluded from totals |
| order_id | Text | No | Globally unique order identifier, repeated across its lines |
| promotion | Value | No | Historical promotion flag, retained in data; not a future model input |

Demo grain: one record per date, product, and store; six products × three stores × 1,096 days = 19,728 records. There are no order IDs because daily summaries do not identify individual orders. All demo revenue is synthetic USD. Promotion days apply a small discount and demand increase in the data generator. Random seed: 2026.

Validation reports input rows, valid rows, invalid rows, duplicate candidates, removed duplicates, negative sales rows, missing dates, and invalid optional quantities. Duplicate candidates are calculated after mapping/normalization; removing them can be wrong for legitimate identical transactions, so removal is opt-in.
