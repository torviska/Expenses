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
            # Tipo 'Shared' (Compartilhado): cada um deve metade.
            if row['Type'] == 'Shared':
                if row['Paid By'] == PERSON1:
                    total_elaine_deve += valor / 2
                else:
                    total_victor_deve += valor / 2
            # Tipo 'Individual': quem não pagou deve o valor total.
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
            # Adiciona ao dataframe atual
            updated_df = pd.
