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
        vals = out[c].map(clean_numeric_string).astype(float)
        if c != "Forward_Horizon_Years":
            vals = vals.where(vals.abs() <= 1, vals / 100)
        out[c] = vals
    return out[COLUMNS]


DISCLAIMER = """
**Important disclaimers**

- **Research and education only.** This tool is not tax, legal, accounting or
  investment advice, and nothing here is an offer or recommendation to buy,
  sell or hold any security. Consult a qualified tax professional and a
  licensed investment advisor before making any decision.
- **AI-generated code.** This software was written with the help of artificial
  intelligence. Although believed to be accurate, it may contain errors,
  "hallucinations", incorrect assumptions or bugs. Verify all results
  independently.
- **Simplified model.** Results rely on your inputs and on simplifying
  assumptions (flat 23.9% long-term and 40.8% short-term tax rates, constant
  returns, no state-specific rules, fees, wash-sale rules, loss
  harvesting or other individual circumstances). Projections are hypothetical;
  actual returns will vary and past performance does not guarantee future
  results.
- **No warranty or liability.** Provided "as is" without warranty of any kind.
  The authors accept no liability for any loss or damage arising from its use.
"""


ABOUT = """
You own a stock that has doubled in value. You're thinking about selling it to
buy something you expect to grow faster. There's a catch: when you sell for a
profit, the government takes a cut called a capital gains tax. That tax shrinks
the money you'd have left to reinvest, so the new investment has to make up
that lost ground. This program works out whether the switch is worth it.

### How it works

1. **You enter your data.** You give it a list of investments, each with its
   ticker symbol, share of your portfolio, how much it has gained, and whether
   you held it long-term (LT) or short-term (ST). This process can be done in
   a separate spreadsheet, which can be uploaded in comma separated values
   (csv) format. You also set your total portfolio value, how much you expect
   to earn by keeping it, how much you'd earn by switching, and how many years
   you'd wait. You can type rows in, upload a spreadsheet file, or paste data.
2. **It figures out the tax.** Short-term gains are taxed at a higher rate
   (40.8%) than long-term gains (23.9%). The program applies the right rate to
   the profit portion of each investment.
3. **It compares two futures.** It calculates what the investment would be
   worth if you hold it, and what it would be worth if you pay the tax and
   redeploy the rest.
4. **It makes a call.** If redeploying wins, it says REDEPLOY. If not, it says
   HOLD. It also shows how many years it would take to earn back the tax.

The results appear in a table with totals for each group.
"""


def about_page():
    st.title("CB Tax Engine: What It Does")
    st.page_link(st.session_state["home_page"], label="Back to the analysis",
                 icon=":material/arrow_back:")
    st.markdown(ABOUT)
    st.divider()
    st.caption(DISCLAIMER)


def run():
    st.set_page_config(page_title="CB Tax Engine", layout="wide")
    home = st.Page(main, title="Analysis", url_path="analysis", default=True)
    about = st.Page(about_page, title="What it does", url_path="about")
    st.session_state["home_page"] = home
    st.session_state["about_page"] = about
    st.navigation([home, about], position="hidden").run()


def main():
    st.title("CB Tax Engine")
    st.warning("Research only. Not tax or investment advice. AI-generated code "
               "that may contain errors. Consult a tax professional and an "
               "investment advisor. See full disclaimers below.")

    if "data" not in st.session_state:
        st.session_state.data = SAMPLE.copy()

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] [data-testid="stPageLink"] p {
            font-size: 1.75rem !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.page_link(st.session_state["about_page"], label="What it does",
                     icon=":material/info:")
        st.header("Controls")
        total = st.slider("Portfolio value ($)", 1_000_000, 100_000_000,
                          1_000_000, step=500_000, format="$%d")
        hold = st.slider("Expected hold return (%)", 0, 50, 10)
        new = st.slider("Expected redeployment return (%)", 0, 50, 15)
        years = st.slider("Forward holding period (years)", 1, 30, 5)
        st.caption("Return and period values are used when an uploaded/pasted "
                   "file lacks those columns.")
    defaults = {
        "Expected_Hold_Return": hold / 100,
        "Expected_New_Return": new / 100,
        "Forward_Horizon_Years": float(years),
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
                            width="stretch", key="editor",
                            column_config={
                                "Expected_New_Return": st.column_config.NumberColumn(
                                    "Expected Redeployment Return"),
                                "Forward_Horizon_Years": st.column_config.NumberColumn(
                                    "Forward Holding Period (years)"),
                            })

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

    st.divider()
    st.caption(DISCLAIMER)


if __name__ == "__main__":
    run()
