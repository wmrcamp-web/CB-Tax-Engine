# CB Tax Engine

Calculates the upfront tax drag of selling a position and compares holding vs. redeploying over a forward horizon (Python 3.13).

## Install

```bash
pip install -r requirements.txt
```

## Run the Streamlit app

```bash
streamlit run streamlit_app.py
```

On Streamlit Community Cloud, set the main file path to `streamlit_app.py` (not `cb_tax_engine/engine.py`).

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
