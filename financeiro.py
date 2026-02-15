import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuração da página para Celular
st.set_page_config(page_title="Expenses Victor & Elaine", page_icon="💶", layout="centered")

st.title("💶 Financeiro Familiar")

# Nomes configuráveis
PERSON1 = "Victor"
PERSON2 = "Elaine"

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ttl=0 evita cache para ver os dados na hora
    return conn.read(ttl="0s").dropna(how="all")

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
            else: # Individual
                if row['Paid By'] == PERSON1:
                    total_elaine_deve += valor
                else:
                    total_victor_deve += valor
        except:
            continue
                
    return total_elaine_deve - total_victor_deve

# --- ENTRADA DE DADOS ---
with st.sidebar:
    st.header("New Expense")
    date = st.date_input("Date", datetime.date.today())
    desc = st.text_input("Description (Ex: Rent, Market)")
    valor = st.number_input("Amount (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Type", ["Shared", "Individual"])
    pago_por = st.selectbox("Paid By", [PERSON1, PERSON2])
    
    if st.button("Register"):
        if desc and valor > 0:
            new_row = pd.DataFrame([{
                "Date": date.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            # Adiciona ao dataframe atual
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # Atualiza a planilha
            conn.update(data=updated_df)
            st.success("Registered!")
            st.rerun()
        else:
            st.error("Please fill in description and amount.")

# --- DASHBOARD ---
if not df.empty:
    # Garantir que a coluna Date seja datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Criar seletor de mês/ano
    meses_disponiveis = df['Date'].dt.strftime('%Y-%m').unique().tolist()
    meses_disponiveis.sort(reverse=True)
    
    mes_atual = st.selectbox("Month Reference", options=meses_disponiveis)
    
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_atual]
    
    # Cartão de Acerto
    acerto = calcular_acerto(df_mes)
    st.subheader(f"Summary: {mes_atual}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Spent", f"€ {df_mes['Amount'].sum():.2f}")
    with col2:
        if acerto > 0:
            st.metric(f"{PERSON2} owes {PERSON1}", f"€ {abs(acerto):.2f}")
        elif acerto < 0:
            st.metric(f"{PERSON1} owes {PERSON2}", f"€ {abs(acerto):.2f}")
        else:
            st.metric("Balance", "€ 0.00")

    # Lista de Gastos
    st.divider()
    st.subheader("History")
    # Formata a data para visualização
    df_display = df_mes.copy()
    df_display['Date'] = df_display['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_display.sort_values("Date", ascending=False), use_container_width=True)
    
else:
    st.info("No expenses found. Use the sidebar to add entries.")
