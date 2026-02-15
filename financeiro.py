import streamlit as st
import pandas as pd
import datetime

# Configuração da página
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

st.title("💶 Financeiro Familiar")

PERSON1 = "Victor"
PERSON2 = "Elaine"

# Link da sua planilha (ajustado para exportação direta)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IydwMAhRfxQxbB6LQJiwwb85r__InSuaZBUA8OkUItQ/export?format=csv"

# Função para carregar dados via URL pública
@st.cache_data(ttl=0)
def carregar_dados():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

df = carregar_dados()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Nova Despesa")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f")
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], format_func=lambda x: "Compartilhado" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar Lançamento"):
        # Se o método conn.update falhou, vamos usar o segredo dos Secrets
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        if desc and valor > 0:
            nova_linha = pd.DataFrame([{
                "Date": data_sel.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            
            try:
                # Tentativa final de salvamento
                conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=df_atualizado)
                st.success("Registrado com sucesso!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar. Verifique se você não deletou a primeira linha da planilha.")
        else:
            st.error("Preencha Descrição e Valor.")

# --- DASHBOARD ---
if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    # Seletor de mês
    meses = df['Date'].dt.strftime('%Y-%m').unique().tolist()
    mes_ref = st.selectbox("Mês", options=sorted(meses, reverse=True))
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_ref]
    
    # Cálculos
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
    else: c2.metric("Saldo", "Zerado")

    st.divider()
    st.dataframe(df_mes.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
