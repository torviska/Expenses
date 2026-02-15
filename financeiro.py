import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Victor & Elaine", page_icon="💶", layout="centered")

# --- FUNÇÃO PARA CONECTAR AO BANCO DE DADOS LOCAL ---
def conectar_banco():
    conn = sqlite3.connect('financeiro.db', check_same_thread=False)
    cursor = conn.cursor()
    # Cria a tabela se ela não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            descricao TEXT,
            valor REAL,
            tipo TEXT,
            pago_por TEXT
        )
    ''')
    conn.commit()
    return conn

conn = conectar_banco()

# --- INTERFACE ---
st.title("💶 Financeiro Familiar")
st.info("Dados armazenados localmente via SQLite (Sem Google Sheets).")

PERSON1 = "Victor"
PERSON2 = "Elaine"

# --- BARRA LATERAL: ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Novo Lançamento")
    data_sel = st.date_input("Data", datetime.date.today())
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (€)", min_value=0.0, format="%.2f", step=0.50)
    tipo = st.selectbox("Tipo", ["Shared", "Individual"], 
                        format_func=lambda x: "Compartilhado (50/50)" if x == "Shared" else "Individual")
    pago_por = st.selectbox("Pago por", [PERSON1, PERSON2])
    
    if st.button("Registrar Lançamento"):
        if desc and valor > 0:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO despesas (data, descricao, valor, tipo, pago_por)
                VALUES (?, ?, ?, ?, ?)
            ''', (data_sel.strftime("%Y-%m-%d"), desc, valor, tipo, pago_por))
            conn.commit()
            st.success("✅ Registrado com sucesso!")
            st.rerun()
        else:
            st.error("⚠️ Preencha a descrição e o valor.")

# --- CARREGAR E EXIBIR DADOS ---
df = pd.read_sql_query("SELECT * FROM despesas", conn)

if not df.empty:
    df['data'] = pd.to_datetime(df['data'])
    
    # Seletor de Mês
    meses = sorted(df['data'].dt.strftime('%Y-%m').unique().tolist(), reverse=True)
    mes_ref = st.selectbox("Mês de Referência", options=meses)
    df_mes = df[df['data'].dt.strftime('%Y-%m') == mes_ref].copy()
    
    # Cálculos de Acerto
    v_deve, e_deve = 0, 0
    for _, r in df_mes.iterrows():
        val = float(r['valor'])
        if r['tipo'] == "Shared":
            if r['pago_por'] == PERSON1: e_deve += val / 2
            else: v_deve += val / 2
        else:
            if r['pago_por'] == PERSON1: e_deve += val
            else: v_deve += val
                
    saldo = e_deve - v_deve
    
    # Dashboard
    c1, c2 = st.columns(2)
    c1.metric("Total no Mês", f"€ {df_mes['valor'].sum():.2f}")
    if saldo > 0:
        c2.metric(f"{PERSON2} deve a {PERSON1}", f"€ {abs(saldo):.2f}")
    elif saldo < 0:
        c2.metric(f"{PERSON1} deve a {PERSON2}", f"€ {abs(saldo):.2f}")
    else:
        c2.metric("Saldo", "Zerado")

    st.divider()
    # Tabela formatada
    df_exibicao = df_mes.copy()
    df_exibicao['data'] = df_exibicao['data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_exibicao.sort_values("data", ascending=False), 
                 use_container_width=True, hide_index=True)
    
    # Botão para limpar tudo (opcional, use com cuidado)
    if st.checkbox("Mostrar opções de exclusão"):
        if st.button("Apagar todos os dados"):
            conn.cursor().execute("DELETE FROM despesas")
            conn.commit()
            st.rerun()
else:
    st.write("Ainda não há lançamentos. Use a barra lateral para começar!")
