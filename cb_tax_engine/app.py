import pandas as pd
import streamlit as st

from cb_tax_engine.engine import process_tax_drag

COLUMNS = [
    "Tkr", "%Allocation", "%Gain", "LT/ST",
    "Expected_Hold_Return", "Expected_New_Return", "Forward_Horizon_Years",
]


def main():
    st.set_page_config(page_title="CB Tax Engine", layout="wide")
    st.title("CB Tax Engine")
    st.caption("Tax drag and redeploy-vs-hold analysis")

    total = st.number_input("Total portfolio value ($)", min_value=0.0, value=1_000_000.0, step=10_000.0)
    lt_tax = st.number_input("Long-term tax rate", min_value=0.0, max_value=1.0, value=0.239, format="%.3f")
    st_tax = st.number_input("Short-term tax rate", min_value=0.0, max_value=1.0, value=0.408, format="%.3f")

    default = pd.DataFrame([{
        "Tkr": "ABC", "%Allocation": "10%", "%Gain": "150%", "LT/ST": "LT",
        "Expected_Hold_Return": 0.06, "Expected_New_Return": 0.10,
        "Forward_Horizon_Years": 10,
    }], columns=COLUMNS)
    df = st.data_editor(default, num_rows="dynamic", width="stretch")

    if st.button("Run analysis"):
        df = df.dropna(subset=["Tkr"])
        if df.empty:
            st.warning("Add at least one position.")
            return
        try:
            result = process_tax_drag(df, total, lt_tax=lt_tax, st_tax=st_tax)
        except Exception as exc:
            st.error(f"Could not process input: {exc}")
            return
        st.dataframe(result, width="stretch", hide_index=True)
