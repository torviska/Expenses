import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

st.title("💶 Financeiro Familiar")

PERSON1 = "Victor"
PERSON2 = "Elaine"

# Criando a conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para buscar dados sem cache para evitar conflitos
def carregar_dados():
    try:
        # Força o refresh dos dados ignorando o cache (ttl=0)
        return conn.read(ttl=0).dropna(how="all")
    except:
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Type', 'Paid By'])

df = carregar_dados()

# --- BARRA LATERAL PARA ENTRADA ---
with st.sidebar:
    st.header("Nova Despesa")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f")
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], format_func=lambda x: "Compartilhado" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar Lançamento"):
        if desc and valor > 0:
            # Criar a nova linha
            nova_linha = pd.DataFrame([{
                "Date": data_sel.strftime("%Y-%m-%d"),
                "Description": desc,
                "Amount": valor,
                "Type": tipo,
                "Paid By": pago_por
            }])
            
            # Combinar com os dados existentes
            df_atualizado = pd.concat([df, nova_linha], ignore_index=True)
            
            try:
                # O segredo: usamos o comando update limpando o cache
                conn.update(data=df_atualizado)
                st.cache_data.clear() # Limpa o cache do Streamlit
                st.success("Registrado com sucesso na planilha!")
                st.rerun()
            except Exception as e:
                st.error("Erro técnico ao salvar. Verifique se o link no Secrets termina com /edit?usp=sharing")
                st.info("Dica: Tente recarregar a página do Streamlit.")
        else:
            st.error("Preencha Descrição e Valor.")

# --- DASHBOARD DE RESUMO ---
if not df.empty:
    st.subheader("Resumo de Gastos")
    
    # Converter data para filtrar por mês
    df['Date'] = pd.to_datetime(df['Date'])
    mes_ref = st.selectbox("Mês", options=df['Date'].dt.strftime('%Y-%m').unique()[::-1])
    df_mes = df[df['Date'].dt.strftime('%Y-%m') == mes_ref]
    
    # Cálculo de quem deve para quem
    v_deve = 0
    e_deve = 0
    for _, r in df_mes.iterrows():
        v = float(r['Amount'])
        if r['Type'] == 'Shared':
            if r['Paid By'] == PERSON1: e_deve += v/2
            else: v_deve += v/2
        else:
            if r['Paid By'] == PERSON1: e_deve += v
            else: v_deve += v
    
    saldo = e_deve - v_deve
    
    c1, c2 = st.columns(2)
    c1.metric("Total no Mês", f"€ {df_mes['Amount'].sum():.2f}")
    if saldo > 0:
        c2.metric(f"{PERSON2} deve a {PERSON1}", f"€ {abs(saldo):.2f}")
    elif saldo < 0:
        c2.metric(f"{PERSON1} deve a {PERSON2}", f"€ {abs(saldo):.2f}")
    else:
        c2.metric("Contas", "Zeradas")

    st.divider()
    st.write("### Histórico Recente")
    st.dataframe(df_mes.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("Planilha vazia. Adicione o primeiro gasto na barra lateral.")
