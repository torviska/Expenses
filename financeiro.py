import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuração da página para Celular
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

st.title("💶 Financeiro Familiar")

# Nomes configuráveis
PERSON1 = "Victor"
PERSON2 = "Elaine"

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="0s").dropna(how="all")

df = get_data()

# --- CÁLCULO DE SALDO ---
def calcular_acerto(data):
    if data.empty: return 0
    # Shared: cada um deve metade. Se eu paguei 100, recebo 50 de volta.
    # Individual: cada um paga o seu. Se paguei o dela, recebo 100.
    total_victor_deve = 0
    total_elaine_deve = 0
    
    for _, row in data.iterrows():
        valor = float(row['Amount'])
        if row['Type'] == 'Shared':
            if row['Paid By'] == PERSON1:
                total_elaine_deve += valor / 2
            else:
                total_victor_deve += valor / 2
        else: # Individual (Paguei algo que era só dela ou vice-versa)
            if row['Paid By'] == PERSON1:
                total_elaine_deve += valor
            else:
                total_victor_deve += valor
                
    return total_elaine_deve - total_victor_deve

# --- INTERFACE ---
with st.sidebar:
    st.header("Nova Despesa")
    date = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição (Ex: Aluguel, Mercado)")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=1.0)
    tipo = st.selectbox("Tipo", ["Shared", "Individual"])
    pago_por = st.selectbox("Quem pagou?", [PERSON1, PERSON2])
    
    if st.button("Registrar Gasto"):
        if desc and valor > 0:
            new_row = pd.DataFrame([{
                "Date": date.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Registrado!")
            st.rerun()
        else:
            st.error("Preencha descrição e valor.")

# --- DASHBOARD ---
if not df.empty:
    # Filtro por mês
    df['Date'] = pd.to_datetime(df['Date'])
    mes_atual = st.selectbox("Mês de Referência", 
                            options=df['Date'].dt.strftime('%Y-%m').unique()[::-1])
    
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_atual]
    
    # Cartão de Acerto
    acerto = calcular_acerto(df_mes)
    st.subheader("Resumo do Mês")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Gasto", f"€ {df_mes['Amount'].sum():.2f}")
    with col2:
        if acerto > 0:
            st.metric("Elaine deve a Victor", f"€ {abs(acerto):.2f}")
        elif acerto < 0:
            st.metric("Victor deve a Elaine", f"€ {abs(acerto):.2f}")
        else:
            st.write("Contas zeradas!")

    # Lista de Gastos
    st.divider()
    st.subheader("Histórico")
    st.dataframe(df_mes.sort_values("Date", ascending=False), use_container_width=True)
    
    if st.button("Limpar dados do mês (Cuidado)"):
        # Lógica para remover apenas os dados do mês selecionado
        df_restante = df[df['Date'].dt.strftime('%Y-%m') != mes_atual]
        conn.update(data=df_restante)
        st.rerun()
else:
    st.info("Nenhum gasto registrado ainda.")
