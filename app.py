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

    # Radio para escolher o tipo de resposta
    tipo_resposta = st.radio("Escolha o tipo de resposta:", ["Resumo simples", "Detalhes adicionais"], index=0)

    if st.button("🔍 Perguntar") and pergunta:
        resumo = df.describe(include="all").to_string()

        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente que explica dados de planilha em linguagem MUITO simples e clara. "
                        "Gere DUAS respostas para cada pergunta: "
                        "1) Um resumo simples, curto, fácil de entender para qualquer pessoa. "
                        "2) Uma explicação mais detalhada, com contexto adicional e comparações. "
                        "Sempre use valores em reais (R$) e não use código."
                    ),
                },
                {
                    "role": "user",
                    "content": f"A planilha tem os seguintes dados resumidos:\n{resumo}\n\nPergunta do usuário: {pergunta}",
                },
            ],
        )

        # A IA deve devolver duas respostas separadas por marcações claras
        texto_completo = resposta.choices[0].message.content

        # Separar por marcação ou palavras-chave se a IA seguir o padrão:
        if "Resumo simples:" in texto_completo and "Detalhes adicionais:" in texto_completo:
            resumo_simples = texto_completo.split("Resumo simples:")[1].split("Detalhes adicionais:")[0].strip()
            detalhes = texto_completo.split("Detalhes adicionais:")[1].strip()
        else:
            # fallback caso a IA não siga o padrão
            resumo_simples = texto_completo
            detalhes = texto_completo

        # Mostrar a resposta escolhida pelo usuário
        if tipo_resposta == "Resumo simples":
            st.write("✅ Resumo simples:")
            st.write(resumo_simples)
            resposta_final = resumo_simples
        else:
            st.write("✅ Detalhes adicionais:")
            st.write(detalhes)
            resposta_final = detalhes

        # Salvar no histórico
        st.session_state["historico"].append(
            {"pergunta": pergunta, "resposta": resposta_final, "tipo": tipo_resposta}
        )

# Mostrar histórico de perguntas
if st.session_state.get("historico"):
    st.subheader("📜 Histórico de Perguntas")
    for h in reversed(st.session_state["historico"][-10:]):  # últimos 10
        st.markdown(f"**Pergunta:** {h['pergunta']}")
        st.markdown(f"**Tipo de resposta:** {h['tipo']}")
        st.markdown(f"**Resposta:** {h['resposta']}")
        st.markdown("---")
