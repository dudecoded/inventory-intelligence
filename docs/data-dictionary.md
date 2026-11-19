# Initial Data Dictionary

The contract evolves after a source dataset is selected. Use stable IDs rather than names as join keys.

## Products
| Field | Type | Meaning |
|---|---|---|
| product_id | string | Stable product identifier |
| product_name | string | Display name |
| category | string | Product category |
| unit_cost | number | Procurement cost per unit |
| selling_price | number | Selling price |
| supplier_id | string | Preferred supplier |
| lead_time_days | integer | Expected delivery lead time |
| reorder_point | number | Business-defined reorder threshold |

## Inventory snapshots
| Field | Type | Meaning |
|---|---|---|
| snapshot_date | date | Snapshot timestamp |
| product_id | string | Product identifier |
| on_hand | number | Sellable stock |
| on_order | number | Ordered but not received |
| reserved | number | Stock committed to orders |

## Sales history
| Field | Type | Meaning |
|---|---|---|
| date | date | Transaction or aggregation date |
| product_id | string | Product identifier |
| units_sold | number | Units sold in period |
| promotion | boolean/string | Promotion indicator, if available |
| unit_price | number | Realized selling price, if available |

## Suppliers
| Field | Type | Meaning |
|---|---|---|
| supplier_id | string | Stable supplier identifier |
| supplier_name | string | Display name |
| lead_time_days | integer | Expected delivery time |
| minimum_order_qty | number | Supplier minimum quantity |

## Quality rules
- Dates must be parseable and consistent.
- Quantities must be numeric and non-negative unless returns are explicitly represented.
- Product IDs must join consistently across tables.
- Missing lead times and costs must be flagged, not replaced with arbitrary values.
