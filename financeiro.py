import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

# --- TRATAMENTO DA CHAVE PRIVADA (RESOLVE VALUEERROR) ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    # Isso garante que os \n da private_key nos Secrets sejam lidos corretamente pelo Python
    st.secrets["connections"]["gsheets"]["private_key"] = st.secrets["connections"]["gsheets"]["private_key"].replace("\\n", "\n")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl=0 garante que ele busque o dado mais fresco do Google Sheets
        data = conn.read(ttl="0s")
        return data.dropna(how="all")
    except:
        # Se a planilha estiver vazia, cria as colunas base
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

df = carregar_dados()

# --- DEFINIÇÕES ---
PERSON1 = "Victor"
PERSON2 = "Elaine"

st.title("💶 Financeiro Familiar")

# --- BARRA LATERAL: ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Novo Lançamento")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição (Ex: Mercado, Aluguel)")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Tipo de Gasto", ["Shared", "Individual"], 
                        format_func=lambda x: "Compartilhado (50/50)" if x == "Shared" else "Individual (Total)")
    pago_por = st.selectbox("Quem pagou?", [PERSON1, PERSON2])
    
    if st.button("Registrar na Planilha"):
        if desc and valor > 0:
            nova_linha = pd.DataFrame([{
                "Date": data_sel.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
