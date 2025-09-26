import pandas as pd
import streamlit as st
from openai import OpenAI

# Inicializar cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="IA Leitora de Planilhas", layout="wide")
st.title("📊 IA Leitora de Planilhas Excel")

# Inicializar variáveis de sessão
if "historico" not in st.session_state:
    st.session_state["historico"] = []

if "respostas_uteis" not in st.session_state:
    st.session_state["respostas_uteis"] = 0

# Upload do arquivo XLSX
uploaded_file = st.file_uploader("📂 Carregue sua planilha (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("✅ Planilha carregada com sucesso!")

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
        st.session_state["respostas_uteis"] = 0
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
                        "Você é um assistente que explica dados de planilha de forma MUITO simples e clara. "
                        "Gere duas respostas: Resumo simples (curto) e Detalhes adicionais. "
                        "Valores em reais (R$), linguagem fácil para qualquer pessoa. "
                        "Não use código ou termos difíceis."
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

        # Botão para marcar como útil
        if st.button("👍 Marcar resposta como útil"):
            st.session_state["respostas_uteis"] += 1
            st.success(f"✅ Resposta marcada como útil! Total: {st.session_state['respostas_uteis']}")

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

# Mostrar contador total de respostas úteis
st.sidebar.metric("Respostas úteis marcadas", st.session_state.get("respostas_uteis", 0))
