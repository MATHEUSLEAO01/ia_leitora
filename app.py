import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Título da aplicação
st.title("Chat com Planilha Excel 📊")

# Carregar planilha
df = pd.read_excel("IA.xlsx")

# API Key do OpenAI (usar variável de ambiente)
api_key = os.environ.get("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")
client = OpenAI(api_key=api_key)

# Input do usuário
pergunta = st.text_input("Digite sua pergunta:")

if st.button("Perguntar"):
    # Preparar contexto com os dados (ex: primeiras 20 linhas)
    contexto = f"Esses são os dados disponíveis:\n{df.head(20).to_string()}\n\nPergunta: {pergunta}"
    
    # Chamar a IA
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um analista de dados especialista em Pandas e Excel."},
            {"role": "user", "content": contexto}
        ]
    )
    
    st.write(resposta.choices[0].message.content)
