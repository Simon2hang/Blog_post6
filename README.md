# Blog Post 6: Matching Parents and Children with SQL

This project uses data from the **Panel Study of Income Dynamics (PSID)** to match parents and children and estimate intergenerational income elasticity (IGE).

The main question is:

**How does the estimated relationship between parent and child income change when income is measured using one year versus multiple years?**

## Data

The project uses three PSID files:

- Parent Identification File
- Individual File
- Family Income Data

## Method

Python and SQLite are used in RStudio to:

- Match parents and children using individual and family IDs
- Use SQL operations such as `SELECT`, `JOIN`, `GROUP BY`, `SUM()`, and `AVG()`
- Construct parent and child labor income
- Compare single-year and multi-year income measures
- Estimate IGE and examine life-cycle bias

## Main Results

- **Single-year IGE (2022): 0.078**
- **Multi-year IGE: 0.142**

The multi-year estimate is higher, suggesting that averaging income across several years provides a more stable measure of long-run economic status.

## Files

```text
code/
  prepare_data.py
  sql_match.py
  ige_analysis.py

data/
  raw_data/
  processed_data/

figures/
  parent_child_income_2022.png
  ige_single_vs_multiyear.png
  ige_by_age_group.png
```

## Reproduction

Run the scripts in this order:

```bash
python code/prepare_data.py
python code/sql_match.py
python code/ige_analysis.py
```
