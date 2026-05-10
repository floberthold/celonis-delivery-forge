# analyze-demand-forecasting skill

This skill provides standardized demand forecasting analysis, model evaluation, and scenario comparison utilities.

## Quick start

```powershell
# Run demand forecasting analysis
python scripts/analyze_demand_forecasting.py --input data/input/demand.csv --model arima

# Compare forecast models
python scripts/analyze_demand_forecasting.py --compare --models "arima,prophet,lstm" --output analysis-report.html

# Generate forecast with scenario parameters
python scripts/analyze_demand_forecasting.py --input data/input/demand.csv --scenario "covid-19-impact"

# Export analysis artifacts
python scripts/analyze_demand_forecasting.py --export-to data/generated/
```

## Artifacts

- `data/input/` - Input data files (demand history, features)
- `data/generated/` - Generated forecasts and analysis outputs
- `.orchestration/forecasting/` - Analysis artifacts and evaluation metrics

## Analysis Components

- Time series decomposition
- Trend and seasonality analysis
- Model selection and validation
- Accuracy metrics (MAE, RMSE, MAPE)
- Scenario-based what-if analysis
- Confidence intervals and uncertainty quantification
