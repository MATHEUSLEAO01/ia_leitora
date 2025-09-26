import pandas as pd
import streamlit as st
from openai import OpenAI

# Inicializar cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configurar página
st.set_page_config(page_title="IA Leitora de Planilhas", layout="wide")
st.title("📊 IA Leitora de Planilhas Excel")

# Upload do arquivo XLSX
uploaded_file = st.file_uploader("📂 Carregue sua planilha (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    # Ler a planilha
    df = pd.read_excel(uploaded_file)
    st.success("✅ Planilha carregada com sucesso!")

    # Inicializar histórico
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    # Sessão de Perguntas Frequentes
    st.sidebar.title("❓ Perguntas Frequentes")
    perguntas_frequentes = [
        "Qual foi o gasto mais alto?",
        "Qual é a média de gastos?",
        "Qual é o gasto mais baixo?",
        "Resumo geral da planilha",
        "Qual produto/vendedor mais gerou gasto?"
    ]

    for p in perguntas_frequentes:
        if st.sidebar.button(p):
            st.session_state["pergunta"] = p

    # Botão para limpar histórico
    if st.sidebar.button("🗑 Limpar Histórico"):
        st.session_state["historico"] = []
        st.success("✅ Histórico limpo!")

    # Caixa de texto para perguntas
    pergunta = st.text_input("Digite sua pergunta:", st.session_state.get("pergunta", ""))

    # Botão para enviar pergunta
    if st.button("🔍 Perguntar") and pergunta:
        resumo = df.describe(include="all").to_string()

        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente que explica dados de planilha "
                        "em linguagem MUITO simples, clara e fácil. "
                        "Explique como se estivesse falando para alguém que não sabe ler bem, "
                        "usando frases curtas e exemplos do dia a dia. "
                        "Sempre mostre valores em reais (R$) e use comparações simples. "
                        "Não use código ou termos difíceis."
                    ),
                },
                {
                    "role": "user",
                    "content": f"A planilha tem os seguintes dados resumidos:\n{resumo}\n\nPergunta do usuário: {pergunta}",
                },
            ],
        )

        resposta_final = resposta.choices[0].message.content
        st.write("✅ Resposta gerada!")
        st.write(resposta_final)

        # Adicionar ao histórico
        st.session_state["historico"].append(
            {"pergunta": pergunta, "resposta": resposta_final}
        )

# Mostrar histórico de perguntas
if st.session_state.get("historico"):
    st.subheader("📜 Histórico de Perguntas")
    for h in reversed(st.session_state["historico"][-10:]):  # mostra últimos 10
        st.markdown(f"**Pergunta:** {h['pergunta']}")
        st.markdown(f"**Resposta:** {h['resposta']}")
        st.markdown("---")
