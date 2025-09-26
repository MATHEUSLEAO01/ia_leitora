import pandas as pd
import streamlit as st
from openai import OpenAI
from gtts import gTTS
import tempfile

# Inicializar cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="IA Leitora de Planilhas", layout="wide")
st.title("📊 IA Leitora de Planilhas Excel com Voz")

# Upload do arquivo XLSX
uploaded_file = st.file_uploader("📂 Carregue sua planilha (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("✅ Planilha carregada com sucesso!")

    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    # FAQ
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

    # Limpar histórico
    if st.sidebar.button("🗑 Limpar Histórico"):
        st.session_state["historico"] = []
        st.success("✅ Histórico limpo!")

    # Caixa de texto
    pergunta = st.text_input("Digite sua pergunta:", st.session_state.get("pergunta", ""))
    tipo_resposta = st.radio("Escolha o tipo de resposta:", ["Resumo simples", "Detalhes adicionais"], index=0)

    if st.button("🔍 Perguntar") and pergunta:
        resumo = df.describe(include="all").to_string()

        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente que explica dados de planilha em português de forma clara e acessível. "
                        "Para cada pergunta, gere DUAS respostas separadas:\n\n"
                        "1) Resumo simples: curto, direto, fácil de entender para qualquer pessoa mas que demonstre os dados de forma clara.\n"
                        "2) Detalhes adicionais: análise completa com base nos dados, incluindo insights, comparações e tendências. "
                        "Explique como interpretar os valores e sugira maneiras de tornar a resposta mais objetiva e certeira. "
                        "Use linguagem simples, mas inclua exemplos concretos de dados e valores reais (R$). "
                        "Evite usar código ou termos técnicos difíceis."
                    ),
                },
                {
                    "role": "user",
                    "content": f"A planilha tem os seguintes dados resumidos:\n{resumo}\n\nPergunta do usuário: {pergunta}",
                },
            ],
        )

        texto_completo = resposta.choices[0].message.content

        # Separar Resumo simples / Detalhes
        if "Resumo simples:" in texto_completo and "Detalhes adicionais:" in texto_completo:
            resumo_simples = texto_completo.split("Resumo simples:")[1].split("Detalhes adicionais:")[0].strip()
            detalhes = texto_completo.split("Detalhes adicionais:")[1].strip()
        else:
            resumo_simples = texto_completo
            detalhes = texto_completo

        # Escolher qual mostrar
        resposta_final = resumo_simples if tipo_resposta == "Resumo simples" else detalhes
        st.write("✅ Resposta gerada!")
        st.write(resposta_final)

        # Text-to-Speech
        tts = gTTS(text=resposta_final, lang='pt')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3")

        # Salvar no histórico
        st.session_state["historico"].append(
            {"pergunta": pergunta, "resposta": resposta_final, "tipo": tipo_resposta}
