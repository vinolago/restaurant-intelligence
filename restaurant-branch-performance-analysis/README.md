# Restaurant Branch Performance Analysis

This project analyzes the performance of a multi-branch restaurant chain (Java House-style) in Kenya, focusing on answering: **"Which branches are making or losing money—and why?"**

## Project Structure

```
restaurant-branch-performance-analysis/
├── data/
│   ├── raw/           # Raw data files
│   └── processed/     # Cleaned data
├── notebooks/         # Jupyter notebooks for analysis
│   ├── 01_data_validation_cleaning.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   ├── 03_profitability_analysis.ipynb
│   └── 04_branch_risk_analysis.ipynb
├── reports/           # Outputs and visuals
│   ├── *.png          # Charts
│   ├── high_risk_branches.csv
│   ├── branch_profitability_summary.csv
│   └── restaurant_insights_report.pdf
└── README.md
```

## Setup

1. Install dependencies: `pip install pandas matplotlib seaborn scikit-learn`
2. Place raw data in `data/raw/`
3. Run notebooks in order.

## Notebooks Overview

1. **Data Validation & Cleaning**: Ensures data integrity.
2. **Exploratory Analysis**: Visual exploration of trends.
3. **Profitability Analysis**: Core analysis of profits/losses.
4. **Branch Risk Analysis**: Predictive modeling for risk.

## Key Outputs

- Visual charts in `/reports/`
- CSV summaries
- PDF executive report

This is a portfolio-grade analytics project demonstrating data cleaning, visualization, and insights generation.