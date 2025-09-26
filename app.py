import pandas as pd
import streamlit as st
from openai import OpenAI
from gtts import gTTS
import tempfile
import matplotlib.pyplot as plt

# -----------------------------
# Inicialização
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="IA Leitora Amigável", layout="wide")

st.title("📊 IA Leitora de Planilhas - Pontuar tech")
st.markdown("Siga os passos: 1️⃣ Carregue sua planilha → 2️⃣ Faça sua pergunta → 3️⃣ Veja e ouça a resposta!")

# -----------------------------
# Sessão de histórico e contadores
# -----------------------------
if "historico" not in st.session_state:
    st.session_state["historico"] = []

if "respostas_uteis" not in st.session_state:
    st.session_state["respostas_uteis"] = 0

if "nao_util" not in st.session_state:
    st.session_state["nao_util"] = False

# -----------------------------
# Upload da planilha
# -----------------------------
uploaded_file = st.file_uploader("📂 Carregue sua planilha Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Planilha carregada com sucesso!")
    except Exception:
        st.error("❌ Não foi possível ler o arquivo. Certifique-se de que é um .xlsx válido.")
        st.stop()

    # -----------------------------
    # FAQ na barra lateral
    # -----------------------------
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

    # Botão de limpar histórico
    if st.sidebar.button("🗑 Limpar Histórico"):
        st.session_state["historico"] = []
        st.session_state["respostas_uteis"] = 0
        st.success("✅ Histórico limpo!")

    st.sidebar.metric("Respostas úteis", st.session_state["respostas_uteis"])

    # -----------------------------
    # Caixa de pergunta
    # -----------------------------
    pergunta = st.text_input("💬 Faça sua pergunta:", st.session_state.get("pergunta", ""))
    tipo_resposta = st.radio("Escolha o tipo de resposta:", ["Resumo simples", "Detalhes adicionais"], index=0)

    if st.button("🔍 Perguntar") and pergunta:
        resumo = df.describe(include="all").to_string()

        # Chamar IA
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente que explica dados de planilha de forma MUITO simples. "
                        "Gere duas respostas separadas:\n"
                        "1) Resumo simples: curto e direto para qualquer pessoa.\n"
                        "2) Detalhes adicionais: análise completa, insights, comparações, tendências e sugestões para tornar a resposta mais objetiva."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Planilha resumida:\n{resumo}\nPergunta: {pergunta}"
                }
            ]
        )

        texto_completo = resposta.choices[0].message.content

        # Separar resumo e detalhes
        if "Resumo simples:" in texto_completo and "Detalhes adicionais:" in texto_completo:
            resumo_simples = texto_completo.split("Resumo simples:")[1].split("Detalhes adicionais:")[0].strip()
            detalhes = texto_completo.split("Detalhes adicionais:")[1].strip()
        else:
            resumo_simples = texto_completo
            detalhes = texto_completo

        resposta_final = resumo_simples if tipo_resposta == "Resumo simples" else detalhes

        # Mostrar resposta
        st.subheader("✅ Resposta:")
        st.write(resposta_final)

        # Botões de feedback
        st.subheader("Feedback da resposta")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Resposta útil"):
                st.session_state["respostas_uteis"] += 1
                st.success(f"Resposta marcada como útil! Total: {st.session_state['respostas_uteis']}")
                # Adicionar ao histórico
                st.session_state["historico"].append(
                    {"pergunta": pergunta, "resposta": resposta_final, "tipo": tipo_resposta, "util": True, "motivo": ""}
                )

        with col2:
            if st.button("👎 Resposta não útil"):
                st.session_state["nao_util"] = True

        if st.session_state["nao_util"]:
            motivo = st.text_input("❌ Por favor, informe o motivo da resposta não ser útil:")
            if motivo:
                st.warning("Obrigado pelo feedback! Registramos sua resposta.")
                st.session_state["historico"].append(
                    {"pergunta": pergunta, "resposta": resposta_final, "tipo": tipo_resposta, "util": False, "motivo": motivo}
                )
                st.session_state["nao_util"] = False

        # Leitura em voz
        tts = gTTS(text=resposta_final, lang='pt')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3")

    # -----------------------------
    # Botões para gráficos e resumo visual
    # -----------------------------
    st.subheader("📊 Visualizações (Ainda em teste - Precisar se bem claro para funcionar)")
    col_graf, col_visual = st.columns(2)

    with col_graf:
        if st.button("📈 Gerar gráfico dos dados"):
            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) > 0:
                fig, ax = plt.subplots()
                df[numeric_cols].sum().sort_values().plot(kind="bar", ax=ax, color="skyblue")
                ax.set_ylabel("Valores")
                ax.set_title("Soma por coluna numérica")
                st.pyplot(fig)
            else:
                st.info("Nenhuma coluna numérica para mostrar gráfico.")

    with col_visual:
        if st.button("🎨 Resumo visual simplificado"):
            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) > 0:
                fig, ax = plt.subplots()
                df[numeric_cols].mean().sort_values().plot(kind="bar", ax=ax, color="lightgreen")
                ax.set_ylabel("Média por coluna")
                ax.set_title("Resumo visual simplificado")
                st.pyplot(fig)
                st.write("Esse gráfico mostra a média de cada coluna numérica da planilha de forma simples.")
            else:
                st.info("Nenhuma coluna numérica para gerar resumo visual.")

# -----------------------------
# Histórico de perguntas
# -----------------------------
if st.session_state.get("historico"):
    st.subheader("📜 Histórico de Perguntas (últimas 10)")
    for h in reversed(st.session_state["historico"][-10:]):
        st.markdown(f"**Pergunta:** {h['pergunta']}")
        st.markdown(f"**Tipo de resposta:** {h['tipo']}")
        st.markdown(f"**Resposta:** {h['resposta']}")
        if not h["util"]:
            st.markdown(f"**Motivo não útil:** {h['motivo']}")
        st.markdown("---")
