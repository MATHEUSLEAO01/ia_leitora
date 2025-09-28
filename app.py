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
st.set_page_config(page_title="IA Leitora de Planilhas - Pontuar tech", layout="wide")

st.title("📊 IA Leitora de Planilhas - Pontuar tech")
st.markdown(
    "Siga os passos: 1️⃣ Carregue sua planilha → 2️⃣ Informe o tipo → 3️⃣ Faça sua pergunta → 4️⃣ Veja e ouça a resposta!"
)

# -----------------------------
# Sessão de histórico e contadores
# -----------------------------
if "historico" not in st.session_state:
    st.session_state["historico"] = []

if "respostas_uteis" not in st.session_state:
    st.session_state["respostas_uteis"] = 0

if "nao_util" not in st.session_state:
    st.session_state["nao_util"] = False

if "info_adicional" not in st.session_state:
    st.session_state["info_adicional"] = ""

if "tipo_planilha" not in st.session_state:
    st.session_state["tipo_planilha"] = ""

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
    # Tipo da planilha
    # -----------------------------
    st.subheader("🗂 Sobre o que se trata esta planilha?")
    tipo_planilha = st.text_input(
        "Ex.: gastos, vendas, estoque, despesas...", st.session_state.get("tipo_planilha", "")
    )
    if tipo_planilha:
        st.session_state["tipo_planilha"] = tipo_planilha

    # -----------------------------
    # Detectar colunas financeiras
    # -----------------------------
    def detectar_colunas_financeiras(df):
        keywords = ["gasto", "valor", "custo", "preço", "despesa", "total"]
        colunas_financeiras = [
            col for col in df.columns if any(k.lower() in col.lower() for k in keywords)
        ]
        # Adiciona colunas numéricas que parecem monetárias
        for col in df.select_dtypes(include="number").columns:
            if df[col].max() > 0 and col not in colunas_financeiras:
                colunas_financeiras.append(col)
        return colunas_financeiras

    col_financeiras = detectar_colunas_financeiras(df)
    st.sidebar.subheader("💰 Colunas financeiras detectadas")
    st.sidebar.write(col_financeiras)

    # Permitir que o usuário confirme/ajuste colunas financeiras
    col_financeiras_ajustadas = st.multiselect(
        "Selecione as colunas financeiras relevantes:", options=df.columns, default=col_financeiras
    )

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

    if st.button("🔍 Perguntar") and pergunta and tipo_planilha:
        # -----------------------------
        # Preparar resumo da planilha
        # -----------------------------
        colunas = df.dtypes.apply(lambda x: str(x)).to_dict()
        df_normalizado = df.copy()
        # Normaliza valores monetários
        for col in col_financeiras_ajustadas:
            df_normalizado[col] = pd.to_numeric(df_normalizado[col], errors="coerce").fillna(0)

        estatisticas_numericas = df_normalizado.describe().to_dict()
        estatisticas_categoricas = df_normalizado.select_dtypes(include=["object", "category"]).describe().to_dict()
        amostra = df_normalizado.head(20).to_dict(orient="records")

        resumo = {
            "tipo_planilha": tipo_planilha,
            "colunas": colunas,
            "colunas_financeiras": col_financeiras_ajustadas,
            "estatisticas_numéricas": estatisticas_numericas,
            "estatisticas_categoricas": estatisticas_categoricas,
            "amostra": amostra,
            "info_adicional": st.session_state.get("info_adicional", "")
        }

        # -----------------------------
        # Prompt otimizado para análise objetiva
        # -----------------------------
        prompt_system = (
            "Você é um assistente especialista em análise de planilhas, com foco em gastos e valores monetários.\n"
            "Regras obrigatórias:\n"
            "1. Responda apenas com base nos dados fornecidos no resumo da planilha.\n"
            "2. Se a resposta não estiver nos dados, diga exatamente: 'Não encontrado na planilha'.\n"
            "3. Nunca invente dados, colunas ou valores que não existam.\n"
            "4. Foque nas colunas financeiras para análise de gastos.\n"
            "5. Organize a resposta em duas partes:\n"
            "   - Resumo simples → frase curta destacando o gasto mais relevante.\n"
            "   - Detalhes adicionais → análise completa: total, máximo, mínimo, média, comparações, padrões e sugestões práticas.\n"
            "6. Se os dados forem insuficientes, explique o que faltou para responder.\n"
            "7. Sempre explique em linguagem clara e objetiva."
        )

        # -----------------------------
        # Chamada à API OpenAI
        # -----------------------------
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": f"Resumo da planilha:\n{resumo}\n\nPergunta: {pergunta}"}
            ]
        )

        texto_completo = resposta.choices[0].message.content

        # -----------------------------
        # Separar resumo e detalhes
        # -----------------------------
        if "Resumo simples:" in texto_completo and "Detalhes adicionais:" in texto_completo:
            resumo_simples = texto_completo.split("Resumo simples:")[1].split("Detalhes adicionais:")[0].strip()
            detalhes = texto_completo.split("Detalhes adicionais:")[1].strip()
        else:
            resumo_simples = texto_completo
            detalhes = texto_completo

        resposta_final = resumo_simples if tipo_resposta == "Resumo simples" else detalhes

        # -----------------------------
        # Mostrar resposta
        # -----------------------------
        st.subheader("✅ Resposta:")
        st.write(resposta_final)

        # -----------------------------
        # Feedback
        # -----------------------------
        st.subheader("Feedback da resposta")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Resposta útil"):
                st.session_state["respostas_uteis"] += 1
                st.success(f"Resposta marcada como útil! Total: {st.session_state['respostas_uteis']}")
                st.session_state["historico"].append(
                    {"pergunta": pergunta, "resposta": resposta_final, "tipo": tipo_resposta, "util": True, "motivo": ""}
                )

        with col2:
            if st.button("👎 Resposta não útil"):
                st.session_state["nao_util"] = True

        # -----------------------------
        # Solicitar mais informações se não útil
        # -----------------------------
        if st.session_state["nao_util"]:
            motivo = st.text_input("❌ Informe o motivo da resposta não ser útil:")
            info_adicional = st.text_area(
                "📝 Forneça mais informações sobre a planilha (colunas relevantes, contexto, moeda, período, etc.):"
            )
            if motivo and info_adicional:
                st.warning("Obrigado pelo feedback! Registramos sua resposta e informações adicionais.")
                st.session_state["historico"].append(
                    {
                        "pergunta": pergunta,
                        "resposta": resposta_final,
                        "tipo": tipo_resposta,
                        "util": False,
                        "motivo": motivo
                    }
                )
                st.session_state["info_adicional"] = info_adicional
                st.session_state["nao_util"] = False

        # -----------------------------
        # Leitura em voz (gTTS seguro)
        # -----------------------------
        if resposta_final.strip():
            try:
                tts = gTTS(text=resposta_final, lang='pt')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.name)
                    st.audio(fp.name, format="audio/mp3")
            except Exception as e:
                st.warning(f"Não foi possível gerar áudio: {e}")
        else:
            st.info("🗣 Nenhum texto para gerar áudio.")

    # -----------------------------
    # Gráficos e resumo visual
    # -----------------------------
    st.subheader("📊 Visualizações")
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
