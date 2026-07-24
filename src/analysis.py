# -*- coding: utf-8 -*-
"""Pure data-summary functions over the anonymized dataset. No plotting here —
   these are shared by the notebook, the dashboard and the slide-deck builder."""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "alunos_anonimizado.csv"

YN_COLUMNS = ["ate", "ase", "rtp", "pei", "tem_pc", "tem_internet"]
BOOL_COLUMNS = ["tem_condicao_saude", "tem_restricao_alimentar"]

# Fields only collected as part of the "fica na escola" (extended-day) enrollment form.
# Confirmed empirically: students who don't stay have these blank ~90%+ of the time,
# so counting them in these rates would understate the true rate among students who
# actually went through the form. Nationality, Problema Saúde and Restr alimentar are
# collected independently of this form and are NOT restricted.
FORM_GATED_COLUMNS = [
    "oferta_escola_1", "oferta_escola_2", "oferta_escola_3", "religiao_moral",
    "ase", "rtp", "pei", "tem_pc", "tem_internet", "autorizacao_saida",
]


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


def fica_escola_breakdown(df: pd.DataFrame) -> pd.Series:
    """Sim vs. Não vs. N/A for 'fica na escola' (stays for extended-day activities).
    The few 'AE' / 'Sim (AE)' / 'Não (AE)' variants are folded into Sim/Não."""
    def normalize(v):
        s = str(v).strip()
        if s == "N/A":
            return "N/A"
        if s.startswith("Sim"):
            return "Sim"
        if s.startswith("Não"):
            return "Não"
        return "N/A"  # bare "AE" - status not actually stated

    return df["fica_escola"].apply(normalize).value_counts()


def ficam_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Students who stay for extended-day activities - the only ones for whom the
    form-gated fields (see FORM_GATED_COLUMNS) were actually collected."""
    fica = df["fica_escola"].astype(str).str.strip()
    return df[fica.str.startswith("Sim")]


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


def rate_by_group(df: pd.DataFrame, yn_col: str, group_col: str = "ano_escolaridade",
                   restrict_to_ficam: bool = True) -> pd.Series:
    """% 'Sim' for a Sim/Não column, grouped by a category (e.g. ano de escolaridade)."""
    if restrict_to_ficam and yn_col in FORM_GATED_COLUMNS:
        df = ficam_subset(df)

    def pct_sim(s):
        s = s.astype(str)
        return (s == "Sim").mean() * 100

    return df.groupby(group_col)[yn_col].apply(pct_sim).round(1)


def yn_overall_rate(df: pd.DataFrame, yn_col: str, restrict_to_ficam: bool = True) -> dict:
    if restrict_to_ficam and yn_col in FORM_GATED_COLUMNS:
        df = ficam_subset(df)
    counts = df[yn_col].astype(str).value_counts()
    total = counts.sum()
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


def yn_overall_count(df: pd.DataFrame, yn_col: str, restrict_to_ficam: bool = True) -> dict:
    """Same as yn_overall_rate but returns raw headcounts alongside %, e.g. for
    'quantos requisitaram ASE'."""
    if restrict_to_ficam and yn_col in FORM_GATED_COLUMNS:
        df = ficam_subset(df)
    counts = df[yn_col].astype(str).value_counts()
    total = counts.sum()
    return {k: {"n": int(v), "pct": round(v / total * 100, 1)} for k, v in counts.items()}


def missing_data_rates(df: pd.DataFrame) -> pd.Series:
    is_na = df.apply(lambda col: col.astype(str).isin(["N/A", "nan", "None"]))
    return (is_na.mean() * 100).round(1).sort_values(ascending=False)


def support_needs_by_nationality(df: pd.DataFrame) -> pd.DataFrame:
    """ASE/RTP/PEI/etc. rates by nationality group - restricted to students who
    actually went through the extended-day form, otherwise 'Estrangeira' would look
    artificially low just because more foreign students happen to not stay."""
    d = ficam_subset(df)
    d = d[d["grupo_nacionalidade"] != "N/A"]
    out = {}
    for col in YN_COLUMNS:
        if col not in d.columns:
            continue
        out[col] = d.groupby("grupo_nacionalidade")[col].apply(
            lambda s: (s.astype(str) == "Sim").mean() * 100
        ).round(1)
    return pd.DataFrame(out)


def religiao_breakdown(df: pd.DataFrame, restrict_to_ficam: bool = True) -> pd.Series:
    if restrict_to_ficam:
        df = ficam_subset(df)
    return df["religiao_moral"].value_counts()


def autorizacao_saida_breakdown(df: pd.DataFrame, restrict_to_ficam: bool = True) -> pd.Series:
    """Distribution of exit-authorization letters (A/B/C/D, or combinations)."""
    if restrict_to_ficam:
        df = ficam_subset(df)
    return df["autorizacao_saida"].value_counts()


def oferta_escola_counts(df: pd.DataFrame, by_ano: bool = True) -> pd.DataFrame:
    """Tidy counts + percentages of each after-school activity choice, by rank
    (1st/2nd/3rd choice) and optionally by ano de escolaridade. Restricted to students
    who stay for extended-day activities - the only ones who made these choices."""
    d = ficam_subset(df)
    choice_cols = {"oferta_escola_1": "1ª escolha", "oferta_escola_2": "2ª escolha",
                   "oferta_escola_3": "3ª escolha"}
    rows = []
    group_cols = ["ano_escolaridade"] if by_ano else []
    for col, label in choice_cols.items():
        sub = d[d[col] != "N/A"]
        if by_ano:
            grouped = sub.groupby(["ano_escolaridade", col]).size()
            totals = sub.groupby("ano_escolaridade").size()
            for (ano, atividade), n in grouped.items():
                rows.append({
                    "ano_escolaridade": ano, "escolha": label, "atividade": atividade,
                    "contagem": int(n), "percentagem": round(n / totals[ano] * 100, 1),
                })
        else:
            counts = sub[col].value_counts()
            total = counts.sum()
            for atividade, n in counts.items():
                rows.append({
                    "escolha": label, "atividade": atividade,
                    "contagem": int(n), "percentagem": round(n / total * 100, 1),
                })
    cols_order = (["ano_escolaridade"] if by_ano else []) + ["escolha", "atividade", "contagem", "percentagem"]
    return pd.DataFrame(rows)[cols_order]


def health_condition_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Health condition categories (never verbatim diagnoses) as counts and % relative
    to ALL students with a known health status (i.e. excluding N/A, not excluding
    non-'ficam' students - health data is collected independently of that form)."""
    known = df[df["categoria_saude"] != "N/A"]
    counts = known["categoria_saude"].value_counts()
    total = counts.sum()
    out = pd.DataFrame({"contagem": counts, "percentagem": (counts / total * 100).round(1)})
    return out.sort_values("contagem", ascending=False)


def dietary_restriction_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Same as health_condition_breakdown, for dietary restrictions."""
    known = df[df["categoria_restricao_alimentar"] != "N/A"]
    counts = known["categoria_restricao_alimentar"].value_counts()
    total = counts.sum()
    out = pd.DataFrame({"contagem": counts, "percentagem": (counts / total * 100).round(1)})
    return out.sort_values("contagem", ascending=False)
