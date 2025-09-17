
import numpy as np
import pandas as pd

def summarize_distributions(
    df: pd.DataFrame,
    cols=None,
    percentiles=(1, 5, 25, 50, 75, 95, 99),
    round_to=None
) -> pd.DataFrame:
    """
   

    Parameters
    ----------
    df : DataFrame
    cols : list[str] | None
        Columns to summarize. If None, uses common defaults.
    percentiles : tuple[int]
        Percentiles to compute (as whole numbers).
    round_to : int | None
        Decimal places to round the result. If None, no rounding.

    Returns
    -------
    DataFrame indexed by variable with columns:
    min, max, p1, p5, p25, p50, p75, p95, p99, spread_p1_p99, iqr
    """
    if cols is None:
        cols = ["normal", "bimodal", "uniform", "exponential", "t_df3", "with_outliers", "lognormal"]

    cols = [c for c in cols if c in df.columns]
    if not cols:
        raise ValueError("None of the requested columns were found in df.")

    # Base stats
    base = df[cols].agg(["min", "max"]).T

    # Percentiles in one vectorized call
    qs = [p / 100 for p in percentiles]
    q = df[cols].quantile(qs)
    q.index = [f"p{int(p)}" for p in percentiles]  # e.g., 0.01 -> 'p1'
    q = q.T

    # Assemble table
    out = pd.concat([base, q], axis=1)

    # Derived spreads
    if {"p99", "p1"}.issubset(out.columns):
        out["spread_p1_p99"] = out["p99"] - out["p1"]
    if {"p75", "p25"}.issubset(out.columns):
        out["iqr"] = out["p75"] - out["p25"]

    # Order/round
    ordered = ["min", "max"] + [f"p{int(p)}" for p in percentiles]
    ordered += [c for c in ["spread_p1_p99", "iqr"] if c in out.columns]
    out = out.loc[:, [c for c in ordered if c in out.columns]]
    out.index.name = "variable"

    if round_to is not None:
        out = out.round(round_to)

    return out


summary = summarize_distributions(df, round_to=4)
summary


