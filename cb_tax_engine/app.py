import pandas as pd
import streamlit as st

from cb_tax_engine import clean_numeric_string, process_tax_drag

COLUMNS = [
    "Tkr", "%Allocation", "%Gain", "LT/ST",
    "Expected_Hold_Return", "Expected_New_Return", "Forward_Horizon_Years",
]

SAMPLE = pd.DataFrame([
    ["ABC", "10%", "150%", "LT", 0.06, 0.10, 10],
    ["XYZ", "5%", "40%", "ST", 0.07, 0.09, 5],
    ["DEF", "8%", "20%", "LT", 0.08, 0.07, 10],
], columns=COLUMNS)


def parse_pasted(text: str, defaults=None) -> pd.DataFrame:
    """Parse CSV/TSV text; missing return/horizon columns are filled from defaults."""
    from io import StringIO

    defaults = defaults or {}
    sep = "\t" if "\t" in text.splitlines()[0] else ","
    df = pd.read_csv(StringIO(text), sep=sep, dtype=str)
    lookup = {c.strip().lower(): c for c in df.columns}
    out = pd.DataFrame()
    missing = []
    for col in COLUMNS:
        if col.lower() in lookup:
            out[col] = df[lookup[col.lower()]]
        elif col in defaults:
            out[col] = defaults[col]
        else:
            missing.append(col)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    for c in COLUMNS[4:]:
        vals = out[c].map(clean_numeric_string) if out[c].dtype == object else out[c]
        if c != "Forward_Horizon_Years":
            vals = vals.where(vals.abs() <= 1, vals / 100)
        out[c] = vals
    return out[COLUMNS]


def main():
    st.set_page_config(page_title="CB Tax Engine", layout="wide")
    st.title("CB Tax Engine")

    if "data" not in st.session_state:
        st.session_state.data = SAMPLE.copy()

    total = st.number_input("Total portfolio value ($)", min_value=0.0,
                            value=1_000_000.0, step=10_000.0)

    st.caption("Defaults used when an uploaded/pasted file lacks these columns "
               "(returns as %, e.g. 6 = 6%).")
    d1, d2, d3 = st.columns(3)
    hold = d1.number_input("Expected hold return (%)", value=6.0, step=0.5)
    new = d2.number_input("Expected new return (%)", value=10.0, step=0.5)
    years = d3.number_input("Forward horizon (years)", value=10.0, min_value=0.0, step=1.0)
    defaults = {
        "Expected_Hold_Return": hold / 100,
        "Expected_New_Return": new / 100,
        "Forward_Horizon_Years": years,
    }

    col1, col2 = st.columns(2)
    if col1.button("Load sample data"):
        st.session_state.data = SAMPLE.copy()
    uploaded = col2.file_uploader("Upload CSV", type="csv")
    pasted = st.text_area("...or paste CSV / tab-separated data (with header row)")

    try:
        if uploaded is not None:
            st.session_state.data = parse_pasted(uploaded.getvalue().decode("utf-8-sig"), defaults)
        elif pasted.strip():
            st.session_state.data = parse_pasted(pasted, defaults)
    except Exception as exc:
        st.error(f"Could not read data: {exc}")

    edited = st.data_editor(st.session_state.data, num_rows="dynamic",
                            width="stretch", key="editor")

    if st.button("Run analysis", type="primary"):
        rows = edited.dropna(how="all")
        if rows.empty:
            st.warning("Add at least one row.")
            return
        try:
            result = process_tax_drag(rows, total)
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            return
        st.dataframe(result, width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
