import pandas as pd
import streamlit as st
from openai import OpenAI

# Inicializar cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Upload do arquivo XLSX
uploaded_file = st.file_uploader("📂 Carregue sua planilha (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    # Ler a planilha
    df = pd.read_excel(uploaded_file)

    st.success("✅ Planilha carregada com sucesso!")

    # Pergunta do usuário
    pergunta = st.text_input("Digite sua pergunta:")

    if pergunta:
        # Criar resumo dos dados (sem mostrar a tabela inteira)
        resumo = df.describe(include="all").to_string()

        # Chamar a IA
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente que explica dados de planilha "
                        "em uma linguagem MUITO simples, clara e fácil. "
                        "Explique como se estivesse falando para alguém que não sabe ler bem, "
                        "usando frases curtas e exemplos do dia a dia. "
                        "Sempre mostre valores em reais (R$) e use comparações fáceis. "
                        "Não use código, termos técnicos ou palavras difíceis."
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

        # Salvar histórico
        if "historico" not in st.session_state:
            st.session_state["historico"] = []
        st.session_state["historico"].append(
            {"pergunta": pergunta, "resposta": resposta_final}
        )

# Mostrar histórico
if "historico" in st.session_state:
    st.subheader("📜 Histórico de Perguntas")
    for h in st.session_state["historico"]:
        st.markdown(f"**Pergunta:** {h['pergunta']}")
        st.markdown(f"**Resposta:** {h['resposta']}")
        st.markdown("---")
