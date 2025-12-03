
import streamlit as st
import json
import os

# Nome do arquivo JSON
DATA_FILE = "empresas.json"

# Função para carregar dados do arquivo JSON
def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Função para salvar dados no arquivo JSON
def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# Interface Streamlit
st.title("Cadastro de Empresas")

# Carregar dados existentes
empresas = carregar_dados()

# Formulário para adicionar empresa
with st.form("form_empresa"):
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    cidade = st.text_input("Cidade")
    submit = st.form_submit_button("Salvar")

if submit:
    nova_empresa = {"nome": nome, "cnpj": cnpj, "cidade": cidade}
    empresas.append(nova_empresa)
    salvar_dados(empresas)
    st.success("Empresa cadastrada com sucesso!")

# Exibir lista de empresas
st.subheader("Empresas cadastradas")
for e in empresas:
