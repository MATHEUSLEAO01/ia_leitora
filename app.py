import pandas as pd
import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Inicialização
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="IA Leitora de Planilhas Avançada", layout="wide")

st.title("📊 IA Leitora de Planilhas Avançada - Pontuar tech")
st.markdown(
    "1️⃣ Carregue sua planilha → 2️⃣ Informe o tipo → 3️⃣ Faça sua pergunta → 4️⃣ Veja e ouça a resposta!"
)

# -----------------------------
# Sessão
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

if uploaded_file:
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
    # Detecção avançada de colunas
    # -----------------------------
    def detectar_colunas_avancado(df):
        keywords = ["gasto", "valor", "custo", "preço", "despesa", "total"]
        colunas_financeiras = []
        colunas_quase_numericas = []

        # Renomeia colunas sem nome
        new_columns = []
        for i, x in enumerate(df.columns):
            if pd.isna(x) or str(x).strip().lower() in ["unnamed", "untitled"]:
                new_columns.append(f"Col_{i}")
            else:
                new_columns.append(x)
        df.columns = new_columns

        for col in df.columns:
            texto_col = str(col).lower()
            if any(k in texto_col for k in keywords):
                colunas_financeiras.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                if df[col].max() > 1:
                    colunas_financeiras.append(col)
            else:
                num_na = pd.to_numeric(df[col], errors='coerce')
                n_na_count = num_na.isna().sum()
                if 0 < n_na_count <= 2:
                    colunas_quase_numericas.append(col)

        if len(colunas_financeiras) == 0:
            colunas_financeiras = df.select_dtypes(include="number").columns.tolist()

        return list(set(colunas_financeiras)), list(set(colunas_quase_numericas)), df

    col_financeiras, col_quase_numericas, df = detectar_colunas_avancado(df)

    st.sidebar.subheader("💰 Colunas financeiras detectadas automaticamente")
    st.sidebar.write(col_financeiras)
    st.sidebar.subheader("🔢 Colunas quase numéricas (descrições possíveis)")
    st.sidebar.write(col_quase_numericas)

    col_financeiras_ajustadas = st.multiselect(
        "Selecione as colunas financeiras relevantes:", options=df.columns, default=col_financeiras
    )

    # -----------------------------
    # FAQ lateral
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
        if st.sidebar.button(p, key=f"faq_{p}"):
            st.session_state["pergunta"] = p

    if st.sidebar.button("🗑 Limpar Histórico"):
        st.session_state["historico"] = []
        st.session_state["respostas_uteis"] = 0
        st.success("✅ Histórico limpo!")

    st.sidebar.metric("Respostas úteis", st.session_state.get("respostas_uteis", 0))

    # -----------------------------
    # Caixa de pergunta
    # -----------------------------
    pergunta = st.text_input("💬 Faça sua pergunta:", st.session_state.get("pergunta", ""))
    tipo_resposta = st.radio("Escolha o tipo de resposta:", ["Resumo simples", "Detalhes adicionais"], index=0)

    if st.button("🔍 Perguntar") and pergunta and tipo_planilha:
        df_normalizado = df.copy()
        for col in col_financeiras_ajustadas:
            df_normalizado[col] = pd.to_numeric(df_normalizado[col], errors="coerce").fillna(0)
            df_normalizado[col] = df_normalizado[col].apply(
                lambda x: round(x, 2) if isinstance(x, float) and len(str(x).split(".")[1]) > 2 else x
            )

        outliers = {}
        for col in col_financeiras_ajustadas:
            if df_normalizado[col].dtype.kind in 'iuf':
                media = df_normalizado[col].mean()
                desvio = df_normalizado[col].std()
                limite_superior = media + 2 * desvio
                limite_inferior = media - 2 * desvio
                outliers[col] = df_normalizado[(df_normalizado[col] > limite_superior) | (df_normalizado[col] < limite_inferior)][col].tolist()

        colunas = df_normalizado.dtypes.apply(lambda x: str(x)).to_dict()
        estatisticas_numericas = df_normalizado.describe().to_dict()

        # ✅ Correção: checagem de colunas categóricas
        df_categoricas = df_normalizado.select_dtypes(include=["object", "category"])
        if not df_categoricas.empty:
            estatisticas_categoricas = df_categoricas.describe().to_dict()
        else:
            estatisticas_categoricas = {"info": "Nenhuma coluna categórica encontrada"}

        amostra = df_normalizado.head(20).to_dict(orient="records")

        resumo = {
            "tipo_planilha": tipo_planilha,
            "colunas": colunas,
            "colunas_financeiras": col_financeiras_ajustadas,
            "colunas_quase_numericas": col_quase_numericas,
            "estatisticas_numéricas": estatisticas_numericas,
            "estatisticas_categoricas": estatisticas_categoricas,
            "amostra": amostra,
            "outliers": outliers,
            "info_adicional": st.session_state.get("info_adicional", "")
        }

        # -----------------------------
        # Prompt ultra avançado
        # -----------------------------
        prompt_system = (
            "Você é um assistente especialista em análise de planilhas de gastos em R$ (Real brasileiro). "
            "Responda apenas com base nos dados fornecidos. Nunca invente valores ou informações. "
            "Se não encontrar a resposta, diga 'Não encontrado na planilha'. "
            "Organize a resposta em duas partes claramente marcadas:\n"
            "- Resumo simples: frase curta destacando o gasto mais relevante ou insight principal.\n"
            "- Detalhes adicionais: total, máximo, mínimo, média, comparações, padrões, alertas de gastos fora do padrão, identificação de outliers, explicação de colunas quase numéricas, arredondamento de valores e análise de tendência simples.\n"
            "Use linguagem clara e objetiva, acessível a qualquer pessoa."
        )

        try:
            resposta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": f"Resumo da planilha:\n{resumo}\nPergunta: {pergunta}"}
                ]
            )
            texto_completo = resposta.choices[0].message.content
        except Exception as e:
            st.error(f"❌ Erro na API OpenAI: {e}")
            st.stop()

        if "Resumo simples:" in texto_completo and "Detalhes adicionais:" in texto_completo:
            resumo_simples = texto_completo.split("Resumo simples:")[1].split("Detalhes adicionais:")[0].strip()
            detalhes = texto_completo.split("Detalhes adicionais:")[1].strip()
        else:
            resumo_simples = texto_completo
            detalhes = texto_completo

        resposta_final = resumo_simples if tipo_resposta == "Resumo simples" else detalhes

        st.subheader("✅ Resposta:")
        st.write(resposta_final)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Resposta útil", key=f"btn_util_{pergunta}"):
                st.session_state["respostas_uteis"] += 1
                st.session_state["historico"].append({
                    "pergunta": pergunta,
                    "resposta": resposta_final,
                    "tipo": tipo_resposta,
                    "util": True,
                    "motivo": ""
                })
                st.success(f"Resposta marcada como útil! Total: {st.session_state['respostas_uteis']}")

        with col2:
            if st.button("👎 Resposta não útil", key=f"btn_nao_util_{pergunta}"):
                st.session_state["nao_util"] = True

        if st.session_state["nao_util"]:
            motivo = st.text_input("❌ Motivo da resposta não ser útil:", key=f"motivo_{pergunta}")
            info_adicional = st.text_area(
                "📝 Mais informações sobre a planilha (colunas, contexto, período, etc.):",
                key=f"info_{pergunta}"
            )
            if motivo and info_adicional:
                st.session_state["historico"].append({
                    "pergunta": pergunta,
                    "resposta": resposta_final,
                    "tipo": tipo_resposta,
                    "util": False,
                    "motivo": motivo
                })
                st.session_state["info_adicional"] = info_adicional
                st.session_state["nao_util"] = False
                st.success("Feedback registrado com sucesso!")

        if resposta_final.strip():
            try:
                tts = gTTS(text=resposta_final, lang='pt')
                mp3_fp = BytesIO()
                tts.write_to_fp(mp3_fp)
                st.audio(mp3_fp.getvalue(), format="audio/mp3")
            except Exception as e:
                st.warning(f"Não foi possível gerar áudio: {e}")

    st.subheader("📊 Visualizações")
    col_graf, col_visual = st.columns(2)

    with col_graf:
        if st.button("📈 Gráfico dos dados", key="grafico"):
            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) > 0:
                fig, ax = plt.subplots()
                df[numeric_cols].sum().sort_values().plot(kind="bar", ax=ax, color="skyblue")
                ax.set_ylabel("Valores")
                ax.set_title("Soma por coluna numérica")
                st.pyplot(fig)
            else:
                st.info("Nenhuma coluna numérica.")

    with col_visual:
        if st.button("🎨 Resumo visual simplificado", key="visual"):
            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) > 0:
                fig, ax = plt.subplots()
                df[numeric_cols].mean().sort_values().plot(kind="bar", ax=ax, color="lightgreen")
                ax.set_ylabel("Média")
                ax.set_title("Resumo visual simplificado")
                st.pyplot(fig)
            else:
                st.info("Nenhuma coluna numérica.")

if st.session_state.get("historico"):
    st.subheader("📜 Histórico de Perguntas (últimas 10)")
    for h in reversed(st.session_state["historico"][-10:]):
        st.markdown(f"**Pergunta:** {h['pergunta']}")
