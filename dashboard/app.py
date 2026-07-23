# -*- coding: utf-8 -*-
"""Interactive dashboard — run with: streamlit run dashboard/app.py"""
import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import analysis as an  # noqa: E402
import style  # noqa: E402

st.set_page_config(page_title="Escola Francisco de Arruda — Diversidade e Apoio", layout="wide")


@st.cache_data
def get_data():
    return an.load_data()


df_full = get_data()

st.title("Diversidade e apoio socioeducativo")
st.caption(
    "Agrupamento de Escolas Francisco de Arruda (Ajuda, Lisboa) — escola TEIP. "
    "Dados anonimizados, 463 alunos, 23 turmas (5º–9º ano + PIEF)."
)

with st.sidebar:
    st.header("Filtros")
    anos = st.multiselect(
        "Ano de escolaridade", sorted(df_full["ano_escolaridade"].unique()),
        default=sorted(df_full["ano_escolaridade"].unique()),
    )
    turmas = st.multiselect(
        "Turma", sorted(df_full["turma"].unique()),
        default=sorted(df_full["turma"].unique()),
    )

df = df_full[df_full["ano_escolaridade"].isin(anos) & df_full["turma"].isin(turmas)]

if df.empty:
    st.warning("Sem alunos para os filtros selecionados.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Alunos (seleção)", len(df))
col2.metric("Turmas (seleção)", df["turma"].nunique())
col3.metric("Índice de diversidade", an.simpson_diversity_index(df))

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Nacionalidade portuguesa vs. estrangeira")
    ratio = an.pt_vs_estrangeira(df)
    fig = go.Figure(
        data=[go.Pie(
            labels=ratio.index, values=ratio.values, hole=0.45,
            marker=dict(colors=[style.PORTUGUESA, style.ESTRANGEIRA],
                        line=dict(color=style.SURFACE, width=2)),
        )]
    )
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
    st.plotly_chart(fig, width='stretch')
    st.caption("Alunos sem nacionalidade registada são excluídos deste rácio.")

with c2:
    st.subheader("Nacionalidades representadas")
    nat = an.nationality_breakdown(df, top_n=7)
    colors = (style.CATEGORICAL * 2)[: len(nat)]
    fig = go.Figure(data=[go.Bar(
        x=nat.values, y=nat.index, orientation="h",
        marker_color=colors, text=nat.values, textposition="outside",
    )])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                       xaxis_title="Nº de alunos", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width='stretch')

st.divider()

c3, c4 = st.columns(2)

with c3:
    st.subheader("Taxa de ASE por ano de escolaridade")
    ase = an.rate_by_group(df, "ase")
    fig = go.Figure(data=[go.Bar(x=ase.index, y=ase.values, marker_color=style.CATEGORICAL[0])])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="% com ASE")
    st.plotly_chart(fig, width='stretch')

with c4:
    st.subheader("Acesso digital em casa")
    pc = an.yn_overall_rate(df, "tem_pc")
    net = an.yn_overall_rate(df, "tem_internet")
    labels = ["Tem PC", "Tem Internet"]
    fig = go.Figure()
    fig.add_bar(name="Sim", x=labels, y=[pc.get("Sim", 0), net.get("Sim", 0)], marker_color=style.SIM)
    fig.add_bar(name="Não", x=labels, y=[pc.get("Não", 0), net.get("Não", 0)], marker_color=style.NAO)
    fig.update_layout(barmode="stack", margin=dict(t=10, b=10, l=10, r=10), yaxis_title="%")
    st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Qualidade dos dados")
missing = an.missing_data_rates(df)
fig = go.Figure(data=[go.Bar(x=missing.values, y=missing.index, orientation="h",
                              marker_color=style.CATEGORICAL[6])])
fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="% em falta (N/A)",
                   yaxis=dict(autorange="reversed"), height=500)
st.plotly_chart(fig, width='stretch')

st.caption(
    "Metodologia de anonimização em `src/anonymize.py`. Nenhum identificador direto "
    "(nome, documento, contactos) está presente neste dataset."
)
