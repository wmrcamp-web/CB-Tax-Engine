import pandas as pd
import streamlit as st

from cb_tax_engine import process_tax_drag

COLUMNS = [
    "Tkr", "%Allocation", "%Gain", "LT/ST",
    "Expected_Hold_Return", "Expected_New_Return", "Forward_Horizon_Years",
]

SAMPLE = pd.DataFrame([
    ["ABC", "10%", "150%", "LT", 0.06, 0.10, 10],
    ["XYZ", "5%", "40%", "ST", 0.07, 0.09, 5],
    ["DEF", "8%", "20%", "LT", 0.08, 0.07, 10],
], columns=COLUMNS)


def parse_pasted(text: str) -> pd.DataFrame:
    """Parse pasted CSV/TSV text into a DataFrame with the required columns."""
    from io import StringIO

    sep = "\t" if "\t" in text.splitlines()[0] else ","
    df = pd.read_csv(StringIO(text), sep=sep, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    df = df[COLUMNS].copy()
    for c in COLUMNS[4:]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    return df


def main():
    st.set_page_config(page_title="CB Tax Engine", layout="wide")
    st.title("CB Tax Engine")

    if "data" not in st.session_state:
        st.session_state.data = SAMPLE.copy()

    total = st.number_input("Total portfolio value ($)", min_value=0.0,
                            value=1_000_000.0, step=10_000.0)

    col1, col2 = st.columns(2)
    if col1.button("Load sample data"):
        st.session_state.data = SAMPLE.copy()
    uploaded = col2.file_uploader("Upload CSV", type="csv")
    pasted = st.text_area("...or paste CSV / tab-separated data (with header row)")

    try:
        if uploaded is not None:
            st.session_state.data = parse_pasted(uploaded.getvalue().decode("utf-8"))
        elif pasted.strip():
            st.session_state.data = parse_pasted(pasted)
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
