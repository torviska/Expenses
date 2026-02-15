import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

# --- FUNÇÃO MÁGICA PARA LIMPAR A CHAVE ---
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    
    # Limpeza profunda da chave privada
    raw_key = s["private_key"]
    
    # Remove \n literais, remove espaços duplos e garante as quebras corretas
    clean_key = raw_key.replace("\\n", "\n").replace(" ", " ")
    if "-----BEGIN PRIVATE KEY-----" not in clean_key:
        clean_key = "-----BEGIN PRIVATE KEY-----\n" + clean_key + "\n-----END PRIVATE KEY-----"
    
    credentials_dict = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": clean_key,
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- CARREGAR DADOS ---
@st.cache_data(ttl=0)
def carregar_dados():
    try:
        client = get_gspread_client()
        sheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

df = carregar_dados()

# --- INTERFACE ---
PERSON1 = "Victor"
PERSON2 = "Elaine"

st.title("💶 Financeiro Familiar")

with st.sidebar:
    st.header("Novo Lançamento")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f")
    tipo = st.selectbox("Tipo", ["Shared", "Individual"])
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar"):
        if desc and valor > 0:
            try:
                client = get_gspread_client()
                sheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).sheet1
                nova_linha = [data_sel.strftime("%Y-%m-%d"), desc, valor, tipo, pago_por]
                sheet.append_row(nova_linha)
                st.success("✅ Registrado!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
        else:
            st.error("⚠️ Preencha os campos.")

# --- TABELA ---
if not df.empty:
    st.write("### Histórico")
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Aguardando dados...")
