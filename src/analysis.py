# -*- coding: utf-8 -*-
"""Pure data-summary functions over the anonymized dataset. No plotting here —
   these are shared by the notebook, the dashboard and the slide-deck builder."""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "alunos_anonimizado.csv"

YN_COLUMNS = ["ate", "ase", "rtp", "pei", "tem_pc", "tem_internet"]
BOOL_COLUMNS = ["tem_condicao_saude", "tem_restricao_alimentar"]


def load_data() -> pd.DataFrame:
    # keep_default_na=False: our own "N/A" marker must stay the literal string
    # "N/A", not get silently upgraded to a real NaN by pandas' default na_values.
    df = pd.read_csv(PROCESSED_CSV, keep_default_na=False, na_values=[])
    for col in BOOL_COLUMNS:
        df[col] = df[col].map({"True": True, "False": False}).astype(bool)
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
    return df


def overview(df: pd.DataFrame) -> dict:
    return {
        "total_alunos": len(df),
        "total_turmas": df["turma"].nunique(),
        "anos_escolaridade": sorted(df["ano_escolaridade"].unique().tolist()),
    }


def nationality_breakdown(df: pd.DataFrame, top_n: int = 7) -> pd.Series:
    """Counts per KNOWN nationality, folding everything past top_n into the shared 'Outra'
    bucket (the same bucket anonymize.py already uses for school-wide rare nationalities).
    Students with no nationality on record are excluded — that's a data-quality gap,
    not a nationality (see missing_data_rates)."""
    counts = df.loc[df["nacionalidade"] != "N/A", "nacionalidade"].value_counts()
    other_count = counts.pop("Outra") if "Outra" in counts.index else 0
    if len(counts) > top_n:
        head = counts.iloc[:top_n].copy()
        other_count += counts.iloc[top_n:].sum()
    else:
        head = counts.copy()
    if other_count:
        head["Outra"] = other_count
    return head.sort_values(ascending=False)


def pt_vs_estrangeira(df: pd.DataFrame, drop_unknown: bool = True) -> pd.Series:
    """Portuguese vs. foreign headcount. By default excludes students with no
    nationality on record — an unknown should never be silently counted as foreign."""
    s = df["grupo_nacionalidade"]
    if drop_unknown:
        s = s[s != "N/A"]
    return s.value_counts()


def simpson_diversity_index(df: pd.DataFrame) -> float:
    """1 - sum(p_i^2) over known nationalities. 0 = everyone the same nationality,
    closer to 1 = more diverse."""
    known = df.loc[df["nacionalidade"] != "N/A", "nacionalidade"]
    p = known.value_counts(normalize=True)
    return round(1 - (p ** 2).sum(), 3)


def rate_by_group(df: pd.DataFrame, yn_col: str, group_col: str = "ano_escolaridade") -> pd.Series:
    """% 'Sim' for a Sim/Não column, grouped by a category (e.g. ano de escolaridade)."""
    def pct_sim(s):
        s = s.astype(str)
        return (s == "Sim").mean() * 100

    return df.groupby(group_col)[yn_col].apply(pct_sim).round(1)


def yn_overall_rate(df: pd.DataFrame, yn_col: str) -> dict:
    counts = df[yn_col].astype(str).value_counts()
    total = counts.sum()
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


def missing_data_rates(df: pd.DataFrame) -> pd.Series:
    is_na = df.apply(lambda col: col.astype(str).isin(["N/A", "nan", "None"]))
    return (is_na.mean() * 100).round(1).sort_values(ascending=False)


def support_needs_by_nationality(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["grupo_nacionalidade"] != "N/A"]
    out = {}
    for col in YN_COLUMNS:
        out[col] = d.groupby("grupo_nacionalidade")[col].apply(
            lambda s: (s.astype(str) == "Sim").mean() * 100
        ).round(1)
    return pd.DataFrame(out)


def religiao_breakdown(df: pd.DataFrame) -> pd.Series:
    return df["religiao_moral"].value_counts()
