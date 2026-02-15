import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

st.title("💶 Financeiro Familiar")

PERSON1 = "Victor"
PERSON2 = "Elaine"

# Conexão segura via Service Account
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        data = conn.read(ttl="0s")
        return data.dropna(how="all")
    except:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

df = carregar_dados()

with st.sidebar:
    st.header("Nova Despesa")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], format_func=lambda x: "Compartilhado" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar Lançamento"):
        if desc and valor > 0:
            nova_linha = pd.DataFrame([{
                "Date": data_sel.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            st.success("Registrado com sucesso!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Preencha Descrição e Valor.")

if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    meses = sorted(df['Date'].dt.strftime('%Y-%m').unique().tolist(), reverse=True)
    mes_ref = st.selectbox("Mês de Referência", options=meses)
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_ref]
    
    # Cálculos de acerto
    v_deve, e_deve = 0, 0
    for _, r in df_mes.iterrows():
        val = float(r['Amount'])
        if r['Type'] == 'Shared':
            if r['Paid By'] == PERSON1: e_deve += val/2
            else: v_deve += val/2
        else:
            if r['Paid By'] == PERSON1: e_deve += val
            else: v_deve += val
    
    saldo = e_deve - v_deve
    
    c1, c2 = st.columns(2)
    c1.metric("Total no Mês", f"€ {df_mes['Amount'].sum():.2f}")
    if saldo > 0: c2.metric(f"{PERSON2} deve a {PERSON1}", f"€ {abs(saldo):.2f}")
    elif saldo < 0: c2.metric(f"{PERSON1} deve a {PERSON2}", f"€ {abs(saldo):.2f}")
    else: c2.metric("Saldo", "Tudo Pago!")

    st.divider()
    df_vis = df_mes.copy()
    df_vis['Date'] = df_vis['Date'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_vis.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Nenhum dado encontrado. Faça seu primeiro lançamento na barra lateral!")
