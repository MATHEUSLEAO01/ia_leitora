import streamlit as st
import pandas as pd
import os
from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ API Key não encontrada. Configure no Secrets.")

client = OpenAI(api_key=api_key)

# Configuração da página
st.set_page_config(page_title="IA Leitora de Excel", layout="wide")
st.title("📊 IA Leitora de Planilhas Excel")

# Upload da planilha
uploaded_file = st.file_uploader("📂 Envie sua planilha Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("✅ Planilha carregada com sucesso!")

    # Estado para histórico
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    # Perguntas frequentes no menu lateral
    st.sidebar.title("❓ Perguntas Frequentes")
    perguntas_frequentes = [
        "Qual cliente teve mais vendas em julho?",
        "Qual é a média da coluna X?",
        "Qual foi o produto mais vendido?",
        "Qual vendedor mais faturou?",
        "Mostre um resumo geral dos dados."
    ]

    for pergunta in perguntas_frequentes:
        if st.sidebar.button(pergunta):
            st.session_state["pergunta"] = pergunta

   # Caixa de texto para perguntas
    pergunta = st.text_input("Digite sua pergunta:", st.session_state.get("pergunta", ""))

    if st.button("🔍 Perguntar") and pergunta:
        with st.spinner("Consultando a IA..."):
            contexto = f"Esses são os dados da planilha (amostra inicial):\n{df.head(20).to_string()}\n\nPergunta: {pergunta}"

            try:
                resposta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é um analista de dados especialista em Pandas e Excel."},
                        {"role": "user", "content": contexto}
                    ]
                )

                resposta_texto = resposta.choices[0].message.content

                # Guardar no histórico
                st.session_state["historico"].append({"pergunta": pergunta, "resposta": resposta_texto})

                st.success("✅ Resposta gerada!")
                st.write(resposta_texto)

            except Exception as e:
                st.error(f"❌ Erro ao consultar a IA: {e}")

    # Histórico
    if st.session_state["historico"]:
        st.subheader("📜 Histórico de Perguntas")
        for item in reversed(st.session_state["historico"][-5:]):
            st.markdown(f"**Pergunta:** {item['pergunta']}")
            st.markdown(f"**Resposta:** {item['resposta']}")
            st.markdown("---")
else:
    st.info("👆 Envie uma planilha Excel para começar.")
