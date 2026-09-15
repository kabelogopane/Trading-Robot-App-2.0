# Historical dataset folder

Place standardized broker-export CSV files in this folder for local research.

## Required columns

```text
timestamp,open,high,low,close
```

The timestamp should identify the candle open time. The application normalizes timestamps to UTC and then converts them to New York time for the 45-minute model.

## MT5 export

When exporting US500 CFD history from MT5, convert the broker export to the required five-column format before committing it here.

Do not commit private account information, login details, API keys, or other sensitive data.

The repository sample data remains the default until a historical dataset is explicitly selected for research.
