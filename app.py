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
