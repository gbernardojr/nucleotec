
import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# ==============================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ==============================
# Substitua pela sua string de conexão do Azure SQL
AZURE_SQL_CONNECTION = "mssql+pyodbc://usuario:senha@servidor.database.windows.net:1433/nome_do_banco?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(AZURE_SQL_CONNECTION)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# ==============================
# MODELOS
# ==============================
class Empresa(Base):
    __tablename__ = 'empresas'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cnpj = Column(String, nullable=False)
    contato = Column(String)
    trilhas = relationship("Trilha", back_populates="empresa")

class Consultor(Base):
    __tablename__ = 'consultores'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String)
    trilhas = relationship("Trilha", back_populates="consultor")

class Ficha(Base):
    __tablename__ = 'fichas'
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(String)
    duracao_horas = Column(Integer)
    trilhas = relationship("Trilha", back_populates="ficha")

class Trilha(Base):
    __tablename__ = 'trilhas'
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'))
    ficha_id = Column(Integer, ForeignKey('fichas.id'))
    consultor_id = Column(Integer, ForeignKey('consultores.id'))
    status = Column(String, default="pendente")
    data_execucao = Column(DateTime)

    empresa = relationship("Empresa", back_populates="trilhas")
    ficha = relationship("Ficha", back_populates="trilhas")
    consultor = relationship("Consultor", back_populates="trilhas")

# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

# ==============================
# INTERFACE STREAMLIT
# ==============================
st.set_page_config(page_title="Sistema de Consultoria", layout="wide")
st.title("📊 Sistema de Consultoria")

menu = st.sidebar.radio("Menu", ["Empresas", "Consultores", "Fichas", "Trilhas", "Histórico"])

# Funções auxiliares
def add_empresa(nome, cnpj, contato):
    empresa = Empresa(nome=nome, cnpj=cnpj, contato=contato)
    session.add(empresa)
    session.commit()

def add_consultor(nome, email):
    consultor = Consultor(nome=nome, email=email)
    session.add(consultor)
    session.commit()

def add_ficha(titulo, descricao, duracao):
    ficha = Ficha(titulo=titulo, descricao=descricao, duracao_horas=duracao)
    session.add(ficha)
    session.commit()

def add_trilha(empresa_id, ficha_id, consultor_id):
    trilha = Trilha(empresa_id=empresa_id, ficha_id=ficha_id, consultor_id=consultor_id)
    session.add(trilha)
    session.commit()

# ==============================
# PÁGINAS
# ==============================
if menu == "Empresas":
    st.header("Cadastro de Empresas")
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    contato = st.text_input("Contato")
    if st.button("Salvar Empresa"):
        add_empresa(nome, cnpj, contato)
        st.success("Empresa cadastrada com sucesso!")

    empresas = session.query(Empresa).all()
    df_empresas = pd.DataFrame([(e.id, e.nome, e.cnpj, e.contato) for e in empresas], columns=["ID", "Nome", "CNPJ", "Contato"])
    st.dataframe(df_empresas)

elif menu == "Consultores":
    st.header("Cadastro de Consultores")
    nome = st.text_input("Nome do Consultor")
    email = st.text_input("Email")
    if st.button("Salvar Consultor"):
        add_consultor(nome, email)
        st.success("Consultor cadastrado com sucesso!")

    consultores = session.query(Consultor).all()
    df_consultores = pd.DataFrame([(c.id, c.nome, c.email) for c in consultores], columns=["ID", "Nome", "Email"])
    st.dataframe(df_consultores)

elif menu == "Fichas":
    st.header("Cadastro de Fichas")
    titulo = st.text_input("Título da Ficha")
    descricao = st.text_area("Descrição")
    duracao = st.number_input("Duração (horas)", min_value=1, step=1)
    if st.button("Salvar Ficha"):
        add_ficha(titulo, descricao, duracao)
        st.success("Ficha cadastrada com sucesso!")

    fichas = session.query(Ficha).all()
    df_fichas = pd.DataFrame([(f.id, f.titulo, f.descricao, f.duracao_horas) for f in fichas], columns=["ID", "Título", "Descrição", "Duração"])
    st.dataframe(df_fichas)

elif menu == "Trilhas":
    st.header("Gerenciar Trilhas")
    empresas = session.query(Empresa).all()
    fichas = session.query(Ficha).all()
    consultores = session.query(Consultor).all()

    empresa_id = st.selectbox("Empresa", [e.id for e in empresas], format_func=lambda x: next(e.nome for e in empresas if e.id == x))
    ficha_id = st.selectbox("Ficha", [f.id for f in fichas], format_func=lambda x: next(f.titulo for f in fichas if f.id == x))
    consultor_id = st.selectbox("Consultor", [c.id for c in consultores], format_func=lambda x: next(c.nome for c in consultores if c.id == x))

    if st.button("Adicionar à Trilha"):
        add_trilha(empresa_id, ficha_id, consultor_id)
        st.success("Ficha adicionada à trilha!")

    trilhas = session.query(Trilha).all()
    df_trilhas = pd.DataFrame([(t.id, t.empresa.nome, t.ficha.titulo, t.consultor.nome, t.status) for t in trilhas], columns=["ID", "Empresa", "Ficha", "Consultor", "Status"])
    st.dataframe(df_trilhas)

elif menu == "Histórico":
    st.header("Histórico da Empresa")
    empresas = session.query(Empresa).all()
    empresa_id = st.selectbox("Selecione a Empresa", [e.id for e in empresas], format_func=lambda x: next(e.nome for e in empresas if e.id == x))

    trilhas = session.query(Trilha).filter(Trilha.empresa_id == empresa_id).all()
    df_hist = pd.DataFrame([(t.ficha.titulo, t.status, t.consultor.nome, t.data_execucao) for t in trilhas], columns=["Ficha", "Status", "Consultor", "Data Execução"])
    st.dataframe(df_hist)
