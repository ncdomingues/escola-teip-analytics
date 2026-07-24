# -*- coding: utf-8 -*-
"""Builds slides/apresentacao.pptx. Run export_charts.py first."""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUT = Path(__file__).resolve().parent / "apresentacao.pptx"

TEAL = RGBColor(0x1C, 0x4F, 0x52)
TEAL_DARK = RGBColor(0x12, 0x35, 0x37)
TERRACOTTA = RGBColor(0xC1, 0x59, 0x2B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x52, 0x51, 0x4E)
BODY_FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

SW, SH = prs.slide_width, prs.slide_height


def add_slide(bg_color):
    slide = prs.slides.add_slide(BLANK)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    bg.fill.solid()
    bg.fill.fore_color.rgb = bg_color
    bg.line.fill.background()
    bg.shadow.inherit = False
    # send to back
    spTree = slide.shapes._spTree
    spTree.remove(bg._element)
    spTree.insert(2, bg._element)
    return slide


def add_text(slide, left, top, width, height, text, size, color, bold=False,
             align=PP_ALIGN.LEFT, font=BODY_FONT, anchor=MSO_ANCHOR.TOP, italic=False,
             line_spacing=1.0):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
        run.font.color.rgb = color
    return box


def add_picture_contain(slide, path, left, top, max_w, max_h):
    from PIL import Image
    with Image.open(path) as im:
        iw, ih = im.size
    ratio = min(max_w / iw, max_h / ih)
    w, h = int(iw * ratio), int(ih * ratio)
    x = left + (max_w - w) // 2
    y = top + (max_h - h) // 2
    slide.shapes.add_picture(str(path), x, y, width=w, height=h)


def footer(slide, text, dark=False):
    add_text(slide, Inches(0.6), Inches(7.08), Inches(9), Inches(0.35), text, 10,
              WHITE if dark else MUTED, italic=True)
    add_text(slide, Inches(11.2), Inches(7.08), Inches(1.5), Inches(0.35),
              "Escola Francisco de Arruda", 10, WHITE if dark else MUTED,
              align=PP_ALIGN.RIGHT, italic=True)


# ---------- 1. Title ----------
s = add_slide(TEAL)
add_text(s, Inches(1), Inches(2.5), Inches(11.3), Inches(1.6),
          "Diversidade e Apoio Socioeducativo", 44, WHITE, bold=True)
add_text(s, Inches(1), Inches(3.85), Inches(11.3), Inches(0.7),
          "Agrupamento de Escolas Francisco de Arruda — Escola TEIP", 22, RGBColor(0xCF, 0xE3, 0xE0))
add_text(s, Inches(1), Inches(4.5), Inches(11.3), Inches(0.5),
          "Ajuda, Lisboa  ·  Dados anonimizados, 463 alunos  ·  Junho–Agosto 2026", 15, RGBColor(0xA9, 0xC7, 0xC4))

# ---------- 2. Contexto TEIP ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "O que é uma escola TEIP", 32, TEAL, bold=True)
body = ("O Programa Territórios Educativos de Intervenção Prioritária (TEIP) apoia agrupamentos "
        "de escolas em contextos socioeconómicos mais vulneráveis, com recursos e acompanhamento "
        "diferenciados.\n\n"
        "Iniciado em 1996 e atualmente na sua 4ª geração (TEIP4, desde 2024/25), o programa "
        "tem como objetivos centrais garantir a inclusão e o sucesso educativo de todos os "
        "alunos e combater o abandono escolar.\n\n"
        "Isto explica a forte diversidade do corpo estudantil do Agrupamento Francisco de Arruda, "
        "e a existência de turmas PIEF (Programa Integrado de Educação e Formação) — refletidas "
        "nos dados analisados nesta apresentação.")
add_text(s, Inches(0.7), Inches(1.7), Inches(7.3), Inches(5), body, 16, INK, line_spacing=1.25)

# right-side stat card
card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.5), Inches(1.9), Inches(4.1), Inches(4.3))
card.fill.solid()
card.fill.fore_color.rgb = RGBColor(0xEC, 0xF2, 0xF1)
card.line.fill.background()
card.shadow.inherit = False
add_text(s, Inches(8.8), Inches(2.2), Inches(3.5), Inches(1),
          "1996", 46, TEAL, bold=True)
add_text(s, Inches(8.8), Inches(2.95), Inches(3.5), Inches(0.6),
          "início do programa TEIP", 13, MUTED)
add_text(s, Inches(8.8), Inches(3.75), Inches(3.5), Inches(1),
          "TEIP4", 46, TERRACOTTA, bold=True)
add_text(s, Inches(8.8), Inches(4.5), Inches(3.5), Inches(0.6),
          "fase atual, desde 2024/25", 13, MUTED)
footer(s, "Fonte: DGE — Direção-Geral da Educação")

# ---------- 3. Visão geral (stat tiles) ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Visão geral dos dados", 32, TEAL, bold=True)
tiles = [
    ("463", "alunos"),
    ("23", "turmas"),
    ("5º–9º + PIEF", "anos de escolaridade"),
    ("0.55", "índice de diversidade\n(nacionalidades)"),
]
tile_w = Inches(2.75)
gap = Inches(0.35)
start_x = Inches(0.7)
for i, (num, label) in enumerate(tiles):
    x = Emu(start_x + i * (tile_w + gap))
    card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.2), tile_w, Inches(3.2))
    card.fill.solid()
    card.fill.fore_color.rgb = TEAL if i % 2 == 0 else TERRACOTTA
    card.line.fill.background()
    card.shadow.inherit = False
    add_text(s, x + Inches(0.15), Inches(2.7), tile_w - Inches(0.3), Inches(1.4),
              num, 34, WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, x + Inches(0.15), Inches(4.1), tile_w - Inches(0.3), Inches(1),
              label, 14, WHITE, align=PP_ALIGN.CENTER)
footer(s, "Turmas do 5º ao 9º ano e turmas PIEF 6º/9º")

# ---------- 3b. Fica na escola ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Fica na escola (atividades de tempos livres)", 28, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_fica_escola.png",
                    Inches(0.7), Inches(1.6), Inches(6.3), Inches(5.2))
add_text(s, Inches(7.4), Inches(2.1), Inches(5.2), Inches(4.8),
          "65% dos alunos ficam na escola para atividades de enriquecimento.\n\n"
          "Confirmámos que campos como ASE, RTP, PEI, acesso a PC/internet, oferta de "
          "escola e autorização de saída só são preenchidos para este grupo — em "
          "média, 90% desses campos ficam em branco para quem não fica.\n\n"
          "Por isso, todas as análises seguintes sobre estes temas são calculadas "
          "apenas sobre os alunos que ficam, para não subestimar as taxas reais.",
          15, INK, line_spacing=1.25)
footer(s, "301 de 463 alunos ficam na escola; 97 não ficam; 65 sem resposta")

# ---------- 4. Nacionalidade PT vs Estrangeira ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Nacionalidade portuguesa vs. estrangeira", 30, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_nationality_ratio.png",
                    Inches(0.7), Inches(1.7), Inches(6.3), Inches(5))
add_text(s, Inches(7.4), Inches(2.3), Inches(5.2), Inches(1),
          "1 em cada 3", 40, TERRACOTTA, bold=True)
add_text(s, Inches(7.4), Inches(3.1), Inches(5.2), Inches(1.4),
          "alunos com nacionalidade registada é de origem estrangeira — "
          "reflexo direto do papel do agrupamento na integração de uma comunidade diversa.",
          16, INK, line_spacing=1.2)
add_text(s, Inches(7.4), Inches(5.3), Inches(5.2), Inches(1),
          "Nota: 64 alunos (13,8%) sem nacionalidade registada foram excluídos "
          "deste rácio para não distorcer o resultado.", 12, MUTED, italic=True)
footer(s, "Rácio calculado sobre alunos com nacionalidade conhecida (n=399)")

# ---------- 5. Nacionalidades representadas ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Nacionalidades representadas", 30, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_nationalities.png",
                    Inches(0.7), Inches(1.6), Inches(11.9), Inches(5.2))
footer(s, "'Outra' agrupa nacionalidades com menos de 3 alunos na escola")

# ---------- 6. ASE ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Apoio socioeconómico (ASE), por ano de escolaridade", 28, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_ase_by_grade.png",
                    Inches(0.7), Inches(1.6), Inches(7.6), Inches(5.2))
add_text(s, Inches(8.6), Inches(2.1), Inches(4.1), Inches(0.9),
          "58%", 40, TERRACOTTA, bold=True)
add_text(s, Inches(8.6), Inches(2.85), Inches(4.1), Inches(0.9),
          "dos alunos que ficam na escola (175 de 301) têm ASE.",
          14, INK, line_spacing=1.2)
add_text(s, Inches(8.6), Inches(3.9), Inches(4.1), Inches(2.7),
          "A Ação Social Escolar (ASE) é o principal indicador de vulnerabilidade "
          "socioeconómica disponível nestes dados — central à missão TEIP.\n\n"
          "A taxa é claramente mais baixa entre alunos estrangeiros (39% vs. 68% "
          "entre os portugueses) — um sinal a investigar: pode refletir menor "
          "candidatura ao ASE, não necessariamente menor necessidade.",
          14, INK, line_spacing=1.2)
footer(s, "ASE = Ação Social Escolar; calculado sobre alunos que ficam na escola")

# ---------- 7. Literacia digital ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Acesso digital em casa", 30, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_digital_access.png",
                    Inches(0.7), Inches(1.6), Inches(7.6), Inches(5.2))
add_text(s, Inches(8.6), Inches(2.1), Inches(4.1), Inches(4.5),
          "O acesso a internet em casa é consideravelmente mais alto do que o acesso "
          "a computador próprio.\n\n"
          "Relevante para qualquer estratégia de ensino ou trabalhos de casa que "
          "dependa de dispositivo próprio — o telemóvel é provavelmente a via de "
          "acesso à internet mais comum nestes casos.",
          15, INK, line_spacing=1.25)
footer(s, "Tem PC / Tem Internet — autodeclarado pelo encarregado de educação")

# ---------- 7b. Oferta de escola ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Oferta de escola: 1ª escolha de atividade", 28, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_oferta_escola.png",
                    Inches(0.7), Inches(1.6), Inches(7.6), Inches(5.2))
add_text(s, Inches(8.6), Inches(2.1), Inches(4.1), Inches(4.5),
          "Teatro é a atividade mais escolhida em 1ª opção, seguida de Música e "
          "Cenografia.\n\n"
          "Nas 2ª e 3ª escolhas a ordem muda (Cenografia passa a liderar) — indício "
          "de que os alunos distribuem as suas 3 escolhas pelas atividades "
          "disponíveis, em vez de repetir a mesma preferência.",
          15, INK, line_spacing=1.25)
footer(s, "Calculado sobre alunos que ficam na escola (n=301)")

# ---------- 7c. Saúde e alimentação ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Condições de saúde e restrições alimentares", 26, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_saude.png",
                    Inches(0.5), Inches(1.5), Inches(6.3), Inches(2.7))
add_picture_contain(s, ASSETS / "chart_dieta.png",
                    Inches(0.5), Inches(4.3), Inches(6.3), Inches(2.6))
add_text(s, Inches(7.1), Inches(1.7), Inches(5.5), Inches(1),
          "81% sem condição de saúde referida", 18, TERRACOTTA, bold=True)
add_text(s, Inches(7.1), Inches(2.5), Inches(5.5), Inches(1.6),
          "Entre os restantes, predominam problemas respiratórios (asma/bronquite) "
          "e défice de atenção/hiperatividade.",
          14, INK, line_spacing=1.2)
add_text(s, Inches(7.1), Inches(4.3), Inches(5.5), Inches(1),
          "91% sem restrição alimentar referida", 18, TERRACOTTA, bold=True)
add_text(s, Inches(7.1), Inches(5.1), Inches(5.5), Inches(1.6),
          "Entre os restantes, destaca-se a não-ingestão de porco/vaca (motivo "
          "cultural ou religioso) — reflexo direto da diversidade da escola.",
          14, INK, line_spacing=1.2)
footer(s, "Categorias amplas, nunca o diagnóstico literal — ver metodologia de anonimização")

# ---------- 8. Qualidade dos dados ----------
s = add_slide(WHITE)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Qualidade dos dados — uma oportunidade de melhoria", 26, TEAL, bold=True)
add_picture_contain(s, ASSETS / "chart_missing_data.png",
                    Inches(0.7), Inches(1.55), Inches(7.6), Inches(5.3))
add_text(s, Inches(8.6), Inches(2.1), Inches(4.1), Inches(4.7),
          "Vários campos têm 30%+ de valores em falta — incluindo nacionalidade "
          "e data de nascimento em alguns casos.\n\n"
          "Recomendação: reforçar a validação obrigatória destes campos no "
          "preenchimento/atualização no Inovar, para melhorar a fiabilidade de "
          "futuras análises e do apoio à decisão.",
          15, INK, line_spacing=1.25)
footer(s, "% de valores 'N/A' por campo, sobre os 463 registos")

# ---------- 9. Conclusões ----------
s = add_slide(TEAL)
add_text(s, Inches(0.7), Inches(0.55), Inches(11.9), Inches(0.9),
          "Conclusões e recomendações", 32, WHITE, bold=True)
bullets = [
    "A escola serve uma população claramente diversa — mais de 10 nacionalidades, ~34% de alunos estrangeiros.",
    "58% dos alunos que ficam na escola têm ASE — e a taxa é quase o dobro entre portugueses (68%) face a estrangeiros (39%): merece investigação se é barreira de acesso, não de necessidade real.",
    "O acesso a computador é o principal fator limitante da literacia digital — mais do que o acesso a internet.",
    "Teatro lidera as primeiras escolhas de atividade; a distribuição muda nas escolhas seguintes.",
    "~19% dos alunos com estado de saúde conhecido têm alguma condição referida, sobretudo respiratória; ~9% têm restrição alimentar, sobretudo por motivo cultural/religioso (porco/vaca).",
    "Melhorar a validação de dados no Inovar (nacionalidade, data de nascimento) tornaria análises futuras mais fiáveis.",
]
box = s.shapes.add_textbox(Inches(0.9), Inches(1.9), Inches(11.5), Inches(4.8))
tf = box.text_frame
tf.word_wrap = True
for i, b in enumerate(bullets):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(16)
    p.line_spacing = 1.15
    run = p.add_run()
    run.text = "•  " + b
    run.font.size = Pt(16)
    run.font.name = BODY_FONT
    run.font.color.rgb = WHITE

# ---------- 10. Obrigado ----------
s = add_slide(TEAL_DARK)
add_text(s, Inches(1), Inches(2.7), Inches(11.3), Inches(1.2),
          "Obrigado", 44, WHITE, bold=True)
add_text(s, Inches(1), Inches(3.9), Inches(11.3), Inches(0.6),
          "Dashboard interativo e código-fonte disponíveis no GitHub", 18, RGBColor(0xCF, 0xE3, 0xE0))
add_text(s, Inches(1), Inches(4.5), Inches(11.3), Inches(0.5),
          "Metodologia de anonimização documentada no repositório — nenhum dado pessoal identificável foi usado.",
          13, RGBColor(0xA9, 0xC7, 0xC4), italic=True)

prs.save(OUT)
print("saved", OUT)
