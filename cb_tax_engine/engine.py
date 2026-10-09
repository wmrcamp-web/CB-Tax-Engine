import pandas as pd
import numpy as np

def clean_numeric_string(val):
    if pd.isna(val) or val is None:
        return np.nan
    val_str = str(val).strip().replace("$", "").replace("%", "").replace(",", "").strip()
    if val_str == "" or val_str.lower() == "nan":
        return np.nan
    try:
        return float(val_str)
    except ValueError:
        return np.nan

def process_tax_drag(df, total_portfolio_value, lt_tax=0.239, st_tax=0.408):
    df = df.copy()

    # Normalize/clean inputs robustly
    df["Clean_Gain_Num"] = df["%Gain"].apply(clean_numeric_string)
    df["Clean_Alloc_Num"] = df["%Allocation"].apply(clean_numeric_string)

    # Fill NaN values to avoid downstream errors
    df["Clean_Gain_Num"] = df["Clean_Gain_Num"].fillna(0.0)
    df["Clean_Alloc_Num"] = df["Clean_Alloc_Num"].fillna(0.0)

    # 1. Tax Friction Logic
    df["Tax_Rate_Applied"] = np.where(df["LT/ST"].astype(str).str.strip().str.upper() == "LT", lt_tax, st_tax)
    df["Gain_Decimal"] = df["Clean_Gain_Num"] / 100.0
    df["Taxable_Portion"] = np.where(df["Gain_Decimal"] >= 0, df["Gain_Decimal"] / (1 + df["Gain_Decimal"]), 0.0)
    df["Upfront_Tax_Drag"] = df["Taxable_Portion"] * df["Tax_Rate_Applied"]
    df["Redeployable_Ratio"] = 1 - df["Upfront_Tax_Drag"]

    # 2. Dynamic Inputs & Allocation Math
    hold_rate = df["Expected_Hold_Return"]
    new_rate = df["Expected_New_Return"]
    horizon = df["Forward_Horizon_Years"]

    allocation_decimal = df["Clean_Alloc_Num"] / 100.0
    df["Starting_Dollar_Value"] = total_portfolio_value * allocation_decimal
    df["Tax_Paid_Dollars"] = df["Starting_Dollar_Value"] * df["Upfront_Tax_Drag"]

    # 3. Breakeven Timeline Math
    log_spread = np.log((1 + new_rate) / (1 + hold_rate))
    df["Breakeven_Years"] = np.where(
        (new_rate > hold_rate) & (df["Redeployable_Ratio"] > 0),
        np.log(1 / df["Redeployable_Ratio"]) / log_spread,
        np.inf
    )

    # 4. Forward Time Horizon Dollar Math
    df["Hold_Value_At_Horizon"] = df["Starting_Dollar_Value"] * ((1 + hold_rate) ** horizon)
    redeploy_starting_dollars = df["Starting_Dollar_Value"] * df["Redeployable_Ratio"]
    df["Redeploy_Value_At_Horizon"] = redeploy_starting_dollars * ((1 + new_rate) ** horizon)
    df["Net_Dollar_Surplus"] = df["Redeploy_Value_At_Horizon"] - df["Hold_Value_At_Horizon"]

    # 5. Logic Engine for Action
    conditions = [
        df["Net_Dollar_Surplus"] > 0,
        df["Net_Dollar_Surplus"] < 0,
        df["Net_Dollar_Surplus"] == 0
    ]
    df["Action"] = np.select(conditions, ["REDEPLOY", "HOLD", "BREAKEVEN"], default="HOLD")

    # Helper to generate output row lists for each subsection
    def get_row_dict(row_data):
        return {
            'Tkr': str(row_data['Tkr']).upper(),
            '%Allocation': f"{row_data['Clean_Alloc_Num']:.1f}%",
            '%Gain': f"{row_data['Clean_Gain_Num']:.1f}%",
            'LT/ST': str(row_data['LT/ST']).upper(),
            'Position Value': f"${row_data['Starting_Dollar_Value']:,.0f}",
            'Tax Paid': f"${row_data['Tax_Paid_Dollars']:,.0f}",
            'Payback (Yrs)': "Never" if row_data['Breakeven_Years'] == np.inf else f"{row_data['Breakeven_Years']:.1f}",
            'Hold Value': f"${row_data['Hold_Value_At_Horizon']:,.0f}",
            'Redeploy Value': f"${row_data['Redeploy_Value_At_Horizon']:,.0f}",
            'Wealth Created': f"+{row_data['Net_Dollar_Surplus']:,.0f}" if row_data['Net_Dollar_Surplus'] > 0 else (f"-${abs(row_data['Net_Dollar_Surplus']):,.0f}" if row_data['Net_Dollar_Surplus'] < 0 else "$0"),
            'ACTION': str(row_data['Action'])
        }

    def get_total_row_dict(sub_df, label):
        sub_alloc = sub_df['Clean_Alloc_Num'].sum()
        sub_pos = sub_df['Starting_Dollar_Value'].sum()
        sub_tax = sub_df['Tax_Paid_Dollars'].sum()
        sub_hold = sub_df['Hold_Value_At_Horizon'].sum()
        sub_redeploy = sub_df['Redeploy_Value_At_Horizon'].sum()
        sub_surplus = sub_df['Net_Dollar_Surplus'].sum()
        return {
            'Tkr': label,
            '%Allocation': f"{(min(100.0, sub_alloc)):.1f}%",
            '%Gain': '',
            'LT/ST': '',
            'Position Value': f"${sub_pos:,.0f}",
            'Tax Paid': f"${sub_tax:,.0f}",
            'Payback (Yrs)': '',
            'Hold Value': f"${sub_hold:,.0f}",
            'Redeploy Value': f"${sub_redeploy:,.0f}",
            'Wealth Created': f"+${sub_surplus:,.0f}" if sub_surplus > 0 else (f"-${abs(sub_surplus):,.0f}" if sub_surplus < 0 else "$0"),
            'ACTION': ''
        }

    def get_empty_row():
        return {k: '' for k in ['Tkr', '%Allocation', '%Gain', 'LT/ST', 'Position Value', 'Tax Paid', 'Payback (Yrs)', 'Hold Value', 'Redeploy Value', 'Wealth Created', 'ACTION']}

    # Split into groups
    redeploy_sub = df[df['Action'] == 'REDEPLOY']
    hold_sub = df[df['Action'] != 'REDEPLOY']

    rows_ordered = []

    # Add redeploy group if it exists
    if not redeploy_sub.empty:
        for _, r in redeploy_sub.iterrows():
            rows_ordered.append(get_row_dict(r))
        # Insert 6 blank input lines above REDEPLOY TOTAL
        for _ in range(6):
            rows_ordered.append(get_empty_row())
        rows_ordered.append(get_total_row_dict(redeploy_sub, "REDEPLOY TOTAL"))

    # Add divider row if both exist
    if not redeploy_sub.empty and not hold_sub.empty:
        rows_ordered.append(get_empty_row())

    # Add hold group if it exists
    if not hold_sub.empty:
        for _, r in hold_sub.iterrows():
            rows_ordered.append(get_row_dict(r))
        # Insert 6 blank input lines above HOLD TOTAL
        for _ in range(6):
            rows_ordered.append(get_empty_row())
        rows_ordered.append(get_total_row_dict(hold_sub, "HOLD TOTAL"))

    # Add Combined Total line 3 rows below the HOLD TOTAL
    for _ in range(3):
        rows_ordered.append(get_empty_row())

    # Compute combined metrics
    rows_ordered.append(get_total_row_dict(df, "COMBINED TOTAL"))

    final_df = pd.DataFrame(rows_ordered)
    return final_df
