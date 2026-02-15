import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

# --- CONFIGURAÇÃO DE ACESSO ---
def get_gspread_client():
    # Puxa os dados dos secrets e corrige a chave privada
    s = st.secrets["connections"]["gsheets"]
    credentials_dict = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": s["private_key"].replace("\\n", "\n"),
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- CARREGAR DADOS ---
def carregar_dados():
    client = get_gspread_client()
    # Abre a planilha pelo link que está no secret
    sheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

try:
    df = carregar_dados()
except:
    df = pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

# --- INTERFACE ---
PERSON1 = "Victor"
PERSON2 = "Elaine"

st.title("💶 Financeiro Familiar")

with st.sidebar:
    st.header("Novo Lançamento")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], 
                        format_func=lambda x: "Compartilhado" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar"):
        if desc and valor > 0:
            client = get_gspread_client()
            sheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"]).sheet1
            
            # Prepara a linha para o Google Sheets
            nova_linha = [
                data_sel.strftime("%Y-%m-%d"),
                desc,
                valor,
                tipo,
                pago_por
            ]
            
            sheet.append_row(nova_linha)
            st.success("✅ Registrado com sucesso!")
            st.rerun()
        else:
            st.error("⚠️ Preencha descrição e valor.")

# --- DASHBOARD ---
if not df.empty:
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'])
    
    meses = sorted(df['Date'].dt.strftime('%Y-%m').unique().tolist(), reverse=True)
    mes_ref = st.selectbox("Mês", options=meses)
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_ref]
    
    # Cálculos
    v_deve, e_deve = 0, 0
    for _, r in df_mes.iterrows():
        val = float(r['Amount'])
        if r['Type'] == "Shared":
            if r['Paid By'] == PERSON1: e_deve += val / 2
            else: v_deve += val / 2
        else:
            if r['Paid By'] == PERSON1: e_deve += val
            else: v_deve += val
                
    saldo = e_deve - v_deve
    
    st.subheader(f"Resumo: {mes_ref}")
    c1, c2 = st.columns(2)
    c1.metric("Total Gasto", f"€ {df_mes['Amount'].sum():.2f}")
    if saldo > 0:
        c2.metric(f"{PERSON2} deve a {PERSON1}", f"€ {abs(saldo):.2f}")
    elif saldo < 0:
        c2.metric(f"{PERSON1} deve a {PERSON2}", f"€ {abs(saldo):.2f}")
    else:
        c2.metric("Saldo", "Zerado")

    st.divider()
    df_ex = df_mes.copy()
    df_ex['Date'] = df_ex['Date'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_ex.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Planilha vazia ou sem dados.")
