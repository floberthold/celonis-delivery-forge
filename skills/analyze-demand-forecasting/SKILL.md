---
name: analyze-demand-forecasting
description: Run demand forecasting analysis, compare forecast models, and perform scenario-based what-if analysis.
---

# Analyze Demand Forecasting Skill

Use this skill when an agent needs to:

- Run demand forecasting with specified models (ARIMA, Prophet, LSTM).
- Compare forecast accuracy across multiple models.
- Perform scenario-based what-if analysis (e.g., COVID impact).
- Evaluate uncertainty and confidence intervals.
- Generate forecasting analysis reports.
- Export results for downstream consumption.

## Tool usage order

1. Run forecasting:
   - `python scripts/analyze_demand_forecasting.py --input <file> --model <arima|prophet|lstm>`
2. Compare models:
   - `python scripts/analyze_demand_forecasting.py --compare --models "arima,prophet,lstm" --output report.html`
3. Scenario analysis:
   - `python scripts/analyze_demand_forecasting.py --input <file> --scenario "<name>"`
4. Export results:
   - `python scripts/analyze_demand_forecasting.py --export-to <dir>`

## Expected outputs

- Forecast predictions and confidence intervals.
- Model accuracy metrics (MAE, RMSE, MAPE).
- Time series decomposition (trend, seasonality, residuals).
- Scenario comparison analysis.
- Visualization outputs (HTML reports, CSV exports).

## Safety rules

- Validate input data quality before forecasting.
- Document model assumptions and parameter choices.
- Include uncertainty quantification in all forecasts.
- Preserve historical data for reproducibility.
- Flag data anomalies or insufficient history warnings.
- Do not use forecasts for high-risk decisions without human review.
