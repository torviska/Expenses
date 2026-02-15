import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuração da página para Celular
st.set_page_config(page_title="Despesas Victor & Elaine", page_icon="💶", layout="centered")

st.title("💶 Financeiro Familiar")

# Nomes dos participantes
PERSON1 = "Victor"
PERSON2 = "Elaine"

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        data = conn.read(ttl="0s")
        if data is None or data.empty:
            return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])
        return data.dropna(how="all")
    except:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

df = get_data()

# --- CÁLCULO DE SALDO ---
def calcular_acerto(data):
    if data.empty: return 0
    total_victor_deve = 0
    total_elaine_deve = 0
    
    for _, row in data.iterrows():
        try:
            valor = float(row['Amount'])
            if row['Type'] == 'Shared':
                if row['Paid By'] == PERSON1:
                    total_elaine_deve += valor / 2
                else:
                    total_victor_deve += valor / 2
            else: 
                if row['Paid By'] == PERSON1:
                    total_elaine_deve += valor
                else:
                    total_victor_deve += valor
        except:
            continue
                
    return total_elaine_deve - total_victor_deve

# --- ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Nova Despesa")
    date = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição (Ex: Aluguel, Mercado)")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], format_func=lambda x: "Compartilhado" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar"):
        if desc and valor > 0:
            new_row = pd.DataFrame([{
                "Date": date.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            # Adiciona ao dataframe atual e salva (Aqui estava o seu erro!)
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Registrado!")
            st.rerun()
        else:
            st.error("Por favor, preencha descrição e valor.")

# --- DASHBOARD ---
if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    meses_disponiveis = df['Date'].dt.strftime('%Y-%m').unique().tolist()
    meses_disponiveis.sort(reverse=True)
    
    mes_atual = st.selectbox("Mês de Referência", options=meses_disponiveis)
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_atual]
    
    acerto = calcular_acerto(df_mes)
    st.subheader(f"Resumo: {mes_atual}")
    
    c1, c2 = st.columns(2)
    c1.metric("Total Gasto", f"€ {df_mes['Amount'].sum():.2f}")
    if acerto > 0:
        c2.metric(f"{PERSON2} deve a {PERSON1}", f"€ {abs(acerto):.2f}")
    elif acerto < 0:
        c2.metric(f"{PERSON1} deve a {PERSON2}", f"€ {abs(acerto):.2f}")
    else:
        c2.metric("Saldo", "€ 0.00")

    st.divider()
    st.subheader("Histórico")
    df_vis = df_mes.copy()
    df_vis['Date'] = df_vis['Date'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_vis.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma despesa encontrada na planilha.")
