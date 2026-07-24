# -*- coding: utf-8 -*-
"""
Reads the real student data (data/raw/, git-ignored) and writes an anonymized,
aggregation-safe dataset to data/processed/ (git-tracked).

Run: python src/anonymize.py
"""
import datetime
import re
import unicodedata
from pathlib import Path

import openpyxl
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_XLSX = PROJECT_ROOT / "data" / "raw" / "DadosAlunosND_23_7_26.xlsx"
OUT_CSV = PROJECT_ROOT / "data" / "processed" / "alunos_anonimizado.csv"
ID_LOOKUP_CSV = PROJECT_ROOT / "data" / "raw" / "id_lookup.csv"  # git-ignored

MIN_NATIONALITY_COUNT = 3  # nationalities with fewer students school-wide get grouped into "Outra"
MIN_CATEGORY_COUNT = 3  # same rule for health/dietary categories - never publish a group of 1-2
REFERENCE_DATE = datetime.date(2026, 7, 23)  # snapshot date, for age calculation


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# Broad clinical categories only - never the verbatim diagnosis text. A student's exact
# free-text health note is special-category data and must never reach the public dataset.
HEALTH_CATEGORIES = [
    ("Hiperatividade / défice de atenção", ["hiperativ", "defice de atencao", "deficie de atencao",
                                             "phda", "ddi", "idha", "ritalina", "opositivo desafiador"]),
    ("Respiratório (asma/bronquite)", ["asma", "bronquite", "respirat"]),
    ("Alergias", ["alergia", "alergic"]),
    ("Neurológico", ["epilepsia", "autis", "asperger", "neurofibromat", "paralisia cerebral", "convuls"]),
    ("Cardíaco", ["coracao", "cardia", "sopro"]),
    ("Endócrino / metabólico", ["diabetes", "tiroide"]),
    ("Hematológico", ["anemia", "fator vii", "falciforme", "talassemia"]),
    ("Genético / cromossómico", ["trissomia"]),
    ("Saúde mental / ansiedade", ["ansiedade"]),
    ("Dificuldades de aprendizagem", ["dislexia", "desortografia"]),
]

DIET_CATEGORIES_NONE = {"nao", "nenhuma", "nada a registar", "n"}


def categorize_health(value):
    if value is None:
        return "N/A"
    s = str(value).strip()
    if s in ("", "N/A"):
        return "N/A"
    low = strip_accents(s).lower()
    if low.startswith("nao") or low in ("nenhuma", "nada a registar"):
        return "Nenhuma"
    for category, keywords in HEALTH_CATEGORIES:
        if any(k in low for k in keywords):
            return category
    return "Outra condição"


def categorize_diet(value):
    if value is None:
        return "N/A"
    s = str(value).strip()
    if s in ("", "N/A"):
        return "N/A"
    low = strip_accents(s).lower()
    if low in DIET_CATEGORIES_NONE:
        return "Nenhuma"
    if "vegetarian" in low:
        return "Vegetariano"
    if "porco" in low or "vaca" in low:
        return "Não come porco/vaca (cultural ou religioso)"
    if any(k in low for k in ("alergia", "marisco", "peixe", "camarao", "lactose",
                               "chocolate", "amendoa", "laranja", "ananas", "grao", "morango")):
        return "Alergia alimentar"
    return "Outra restrição"


def suppress_small_groups(series, min_count, other_label):
    """Folds any category with fewer than min_count students into other_label.
    'N/A' and 'Nenhuma' are never suppressed - they aren't identifying groups."""
    counts = series.value_counts()
    small = set(counts[counts < min_count].index) - {"N/A", "Nenhuma"}
    return series.apply(lambda v: other_label if v in small else v)


def load_all_sheets(path):
    wb = openpyxl.load_workbook(path, data_only=False)
    records = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        headers = [ws.cell(row=2, column=c).value for c in range(1, 29)]
        for r in range(3, ws.max_row + 1):
            aluno = ws.cell(row=r, column=1).value
            if not aluno or not str(aluno).strip():
                continue
            row = {headers[c - 1]: ws.cell(row=r, column=c).value for c in range(1, 29)}
            row["Turma"] = sheet_name.strip()
            row["Ano"] = re.match(r"(\d+|PIEF \d+)", sheet_name.strip()).group(1) if re.match(r"(\d+|PIEF \d+)", sheet_name.strip()) else sheet_name.strip()
            records.append(row)
    return pd.DataFrame(records)


PLAUSIBLE_AGE_RANGE = (3, 20)  # 5º-9º ano + PIEF; anything outside this is a source-data error


def compute_age(birth_value):
    if not isinstance(birth_value, (datetime.date, datetime.datetime)):
        return None
    birth_date = birth_value.date() if isinstance(birth_value, datetime.datetime) else birth_value
    age = REFERENCE_DATE.year - birth_date.year
    if (REFERENCE_DATE.month, REFERENCE_DATE.day) < (birth_date.month, birth_date.day):
        age -= 1
    if not (PLAUSIBLE_AGE_RANGE[0] <= age <= PLAUSIBLE_AGE_RANGE[1]):
        return None  # implausible birthdate in the source file (typo) -> treat as missing
    return age


def has_content_flag(value):
    """True if the field holds a real (non-N/A, non-'Não') note."""
    if value is None:
        return False
    s = str(value).strip()
    if s in ("", "N/A"):
        return False
    return not s.lower().startswith("não")


def anonymize(df):
    out = pd.DataFrame()

    out["id_aluno"] = [f"ALU-{i+1:04d}" for i in range(len(df))]
    ID_LOOKUP_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"id_aluno": out["id_aluno"], "nome_real": df["Aluno"]}).to_csv(
        ID_LOOKUP_CSV, index=False, encoding="utf-8-sig"
    )

    out["turma"] = df["Turma"]
    out["ano_escolaridade"] = df["Ano"]
    out["idade"] = df["Nascim."].apply(compute_age)

    # 3-state group, computed on the RAW nationality so missing data is never folded
    # into "Estrangeira" — only genuinely known foreign nationalities count as such.
    out["grupo_nacionalidade"] = df["Nacionalidade"].apply(
        lambda n: "N/A" if n == "N/A" or pd.isna(n) else ("Portuguesa" if n == "Portuguesa" else "Estrangeira")
    )

    nat_counts = df["Nacionalidade"].value_counts()
    small_nats = set(nat_counts[nat_counts < MIN_NATIONALITY_COUNT].index) - {"N/A"}
    out["nacionalidade"] = df["Nacionalidade"].apply(
        lambda n: "Outra" if n in small_nats else n
    )

    out["fica_escola"] = df["Fica Escola"]
    out["ate"] = df["ATE"]
    out["ase"] = df["ASE"]
    out["rtp"] = df["RTP"]
    out["pei"] = df["PEI"]
    out["tem_pc"] = df["Tem PC"]
    out["tem_internet"] = df["Tem Internet"]
    out["religiao_moral"] = df["Religião"]
    out["autorizacao_saida"] = df["Autorização de saída"]

    out["tem_condicao_saude"] = df["Problema Saúde"].apply(has_content_flag)
    out["tem_restricao_alimentar"] = df["Restr alimentar"].apply(has_content_flag)
    out["categoria_saude"] = suppress_small_groups(
        df["Problema Saúde"].apply(categorize_health), MIN_CATEGORY_COUNT, "Outra condição"
    )
    out["categoria_restricao_alimentar"] = suppress_small_groups(
        df["Restr alimentar"].apply(categorize_diet), MIN_CATEGORY_COUNT, "Outra restrição"
    )

    def norm_activity(v):
        # fixes a stray casing typo in the source ("musica" vs "Música") without
        # inventing categories - anything else passes through untouched.
        if isinstance(v, str) and strip_accents(v).lower() == "musica":
            return "Música"
        return v

    out["oferta_escola_1"] = df["Oferta de Escola 1"].apply(norm_activity)
    out["oferta_escola_2"] = df["Oferta de Escola 2"].apply(norm_activity)
    out["oferta_escola_3"] = df["Oferta de Escola 3"].apply(norm_activity)

    return out


def main():
    df = load_all_sheets(RAW_XLSX)
    anon = anonymize(df)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    anon.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"{len(anon)} alunos processados -> {OUT_CSV}")
    print(f"Tabela de correspondência (NÃO commitar) -> {ID_LOOKUP_CSV}")

    n_no_age = anon["idade"].isna().sum()
    n_no_nat = (anon["grupo_nacionalidade"] == "N/A").sum()
    print(f"Nota de qualidade de dados: {n_no_age} alunos sem idade válida "
          f"(data de nascimento em falta ou implausível na fonte), "
          f"{n_no_nat} alunos sem nacionalidade registada.")


if __name__ == "__main__":
    main()
