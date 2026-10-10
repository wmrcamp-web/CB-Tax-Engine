# CB Tax Engine

Calculates the upfront tax drag of selling a position and compares holding vs. redeploying over a forward horizon (Python 3.13).

## Install

```bash
pip install -r requirements.txt
```

## Usage

```python
import pandas as pd
from cb_tax_engine import process_tax_drag

df = pd.DataFrame([{
    "Tkr": "ABC", "%Allocation": "10%", "%Gain": "150%", "LT/ST": "LT",
    "Expected_Hold_Return": 0.06, "Expected_New_Return": 0.10,
    "Forward_Horizon_Years": 10,
}])
print(process_tax_drag(df, total_portfolio_value=1_000_000))
```

Required columns: `Tkr`, `%Allocation`, `%Gain`, `LT/ST`, `Expected_Hold_Return`, `Expected_New_Return`, `Forward_Horizon_Years`.

## Streamlit app

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Enter the total portfolio value, then load sample data, upload/paste a CSV (with the required columns as header), or edit rows in the table. Click **Run analysis** to see the output of `process_tax_drag`.

## Disclaimer

This project is for research and educational purposes only. It is not tax, legal, accounting or investment advice and is not a recommendation to buy, sell or hold any security. Consult a qualified tax professional and a licensed investment advisor before making decisions.

The code was generated with the help of AI. While believed to be accurate, it may contain errors, hallucinations or incorrect assumptions; verify all results independently. The model uses simplified flat tax rates and constant returns, and projections are hypothetical. Provided "as is" without warranty; the authors accept no liability for its use.
