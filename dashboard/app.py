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

fica = an.fica_escola_breakdown(df)
n_ficam = int(fica.get("Sim", 0))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Alunos (seleção)", len(df))
col2.metric("Turmas (seleção)", df["turma"].nunique())
col3.metric("Índice de diversidade", an.simpson_diversity_index(df))
col4.metric("Ficam na escola", f"{n_ficam} ({round(n_ficam/len(df)*100)}%)")

st.info(
    "ASE, RTP, PEI, PC/Internet, oferta de escola, religião e autorização de saída só são "
    "preenchidos para alunos que **ficam na escola** para atividades de tempos livres — "
    "por isso essas taxas, abaixo, são calculadas apenas sobre esse grupo.",
    icon="ℹ️",
)

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
    st.subheader("Ação Social Escolar (ASE)")
    ase_counts = an.yn_overall_count(df, "ase")
    n_sim = ase_counts.get("Sim", {}).get("n", 0)
    pct_sim = ase_counts.get("Sim", {}).get("pct", 0)
    st.metric("Alunos com ASE (entre os que ficam)", f"{n_sim} ({pct_sim}%)")
    ase = an.rate_by_group(df, "ase")
    fig = go.Figure(data=[go.Bar(x=ase.index, y=ase.values, marker_color=style.CATEGORICAL[0])])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="% com ASE")
    st.plotly_chart(fig, width='stretch')

with c4:
    st.subheader("Acesso digital em casa")
    pc = an.yn_overall_count(df, "tem_pc")
    net = an.yn_overall_count(df, "tem_internet")
    labels = ["Tem PC", "Tem Internet"]
    sim_vals = [pc.get("Sim", {}).get("pct", 0), net.get("Sim", {}).get("pct", 0)]
    nao_vals = [pc.get("Não", {}).get("pct", 0), net.get("Não", {}).get("pct", 0)]
    fig = go.Figure()
    fig.add_bar(name="Sim", x=labels, y=sim_vals, marker_color=style.SIM)
    fig.add_bar(name="Não", x=labels, y=nao_vals, marker_color=style.NAO)
    fig.update_layout(barmode="stack", margin=dict(t=10, b=10, l=10, r=10), yaxis_title="%")
    st.plotly_chart(fig, width='stretch')
    st.caption(
        f"Tem PC: {pc.get('Sim', {}).get('n', 0)} alunos  ·  "
        f"Tem Internet: {net.get('Sim', {}).get('n', 0)} alunos (entre os que ficam)"
    )

st.divider()

c5, c6 = st.columns(2)

with c5:
    st.subheader("PEI e RTP")
    for col, nome in [("pei", "PEI"), ("rtp", "RTP")]:
        counts = an.yn_overall_count(df, col)
        n = counts.get("Sim", {}).get("n", 0)
        pct = counts.get("Sim", {}).get("pct", 0)
        st.metric(nome, f"{n} alunos ({pct}%)")

with c6:
    st.subheader("Autorização de saída")
    auth = an.autorizacao_saida_breakdown(df)
    fig = go.Figure(data=[go.Bar(x=auth.values, y=auth.index, orientation="h",
                                  marker_color=style.CATEGORICAL[5])])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Nº de alunos",
                       yaxis=dict(autorange="reversed"), height=320)
    st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Oferta de escola: escolhas de atividades")
oferta = an.oferta_escola_counts(df, by_ano=False)
tab1, tab2, tab3 = st.tabs(["1ª escolha", "2ª escolha", "3ª escolha"])
for tab, label in zip([tab1, tab2, tab3], ["1ª escolha", "2ª escolha", "3ª escolha"]):
    with tab:
        sub = oferta[oferta["escolha"] == label]
        fig = go.Figure(data=[go.Bar(
            x=sub["atividade"], y=sub["percentagem"], marker_color=style.CATEGORICAL[:len(sub)],
            text=sub["contagem"], textposition="outside",
        )])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), yaxis_title="% dos alunos")
        st.plotly_chart(fig, width='stretch', key=f"oferta_{label}")

st.divider()

c7, c8 = st.columns(2)

with c7:
    st.subheader("Condições de saúde")
    saude = an.health_condition_breakdown(df)
    pct_nenhuma = saude.loc["Nenhuma", "percentagem"] if "Nenhuma" in saude.index else None
    if pct_nenhuma is not None:
        st.caption(f"{pct_nenhuma}% dos alunos (com estado de saúde conhecido) não têm nenhuma condição referida.")
    sub = saude.drop(index="Nenhuma", errors="ignore")
    fig = go.Figure(data=[go.Bar(
        x=sub["percentagem"], y=sub.index, orientation="h", marker_color=style.CATEGORICAL[3],
    )])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="% dos alunos",
                       yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width='stretch')
    st.caption("Categorias amplas, nunca o diagnóstico literal - ver metodologia de anonimização.")

with c8:
    st.subheader("Restrições alimentares")
    dieta = an.dietary_restriction_breakdown(df)
    pct_nenhuma = dieta.loc["Nenhuma", "percentagem"] if "Nenhuma" in dieta.index else None
    if pct_nenhuma is not None:
        st.caption(f"{pct_nenhuma}% dos alunos (com estado alimentar conhecido) não têm nenhuma restrição referida.")
    sub = dieta.drop(index="Nenhuma", errors="ignore")
    fig = go.Figure(data=[go.Bar(
        x=sub["percentagem"], y=sub.index, orientation="h", marker_color=style.CATEGORICAL[4],
    )])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="% dos alunos",
                       yaxis=dict(autorange="reversed"))
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
