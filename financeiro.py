import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

# --- TRATAMENTO DA CHAVE PRIVADA ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    st.secrets["connections"]["gsheets"]["private_key"] = st.secrets["connections"]["gsheets"]["private_key"].replace("\\n", "\n")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl="0s")
        return data.dropna(how="all")
    except:
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
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], 
                        format_func=lambda x: "Compartilhado" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar"):
        if desc and valor > 0:
            # Aqui estava o erro de fechamento de chaves/parênteses
            nova_linha = pd.DataFrame([{
                "Date": data_sel.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            
            st.success("✅ Registrado!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("⚠️ Preencha descrição e valor.")

# --- DASHBOARD ---
if not df.empty:
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
    st.info("Planilha vazia. Adicione o primeiro gasto!")
