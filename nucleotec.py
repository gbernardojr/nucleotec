import streamlit as st
import pyodbc
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados Azure SQL
def get_connection():
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    driver = '{ODBC Driver 18 for SQL Server}'
    
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(connection_string)

# Função para executar consultas
def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            columns = [column[0] for column in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame.from_records(data, columns=columns)
            conn.commit()
            conn.close()
            return df
        else:
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"Erro ao executar a consulta: {str(e)}")
        conn.rollback()
        conn.close()
        return False

# Configuração da página
st.set_page_config(page_title="Sistema de Gestão de Fichas Técnicas", layout="wide")

# Menu principal
def main():
    st.sidebar.title("Menu")
    menu_options = {
        "Empresas Promotoras": empresa_promotora_page,
        "Programas": programa_page,
        "Categorias de Serviço": categoria_servico_page,
        "Tipos de Serviço": tipo_servico_page,
        "Instrumentos": instrumento_page,
        "Modalidades": modalidade_page,
        "Portes Empresariais": porte_empresarial_page,
        "Setores": setor_page,
        "Macro Segmentos": macro_segmento_page,
        "Fichas Técnicas": ficha_tecnica_page
    }
    
    selected_page = st.sidebar.selectbox("Selecione uma opção", list(menu_options.keys()))
    menu_options[selected_page]()

# Páginas CRUD para cada tabela
def empresa_promotora_page():
    st.title("Gestão de Empresas Promotoras")
    
    # Operações CRUD
    operation = st.radio("Operação", ["Criar", "Ler", "Atualizar", "Deletar"])
    
    if operation == "Criar":
        st.subheader("Adicionar Nova Empresa Promotora")
        nome = st.text_input("Nome da Empresa Promotora")
        sigla = st.text_input("Sigla", max_chars=10)
        
        if st.button("Salvar"):
            query = "INSERT INTO EmpresaPromotora (nomeEmpresaPromotora, siglaEmpresaPromotora) VALUES (?, ?)"
            if execute_query(query, (nome, sigla)):
                st.success("Empresa Promotora adicionada com sucesso!")
    
    elif operation == "Ler":
        st.subheader("Lista de Empresas Promotoras")
        query = "SELECT idEmpresaPromotora, nomeEmpresaPromotora, siglaEmpresaPromotora FROM EmpresaPromotora"
        df = execute_query(query, fetch=True)
        st.dataframe(df)
    
    elif operation == "Atualizar":
        st.subheader("Atualizar Empresa Promotora")
        query = "SELECT idEmpresaPromotora, nomeEmpresaPromotora FROM EmpresaPromotora"
        empresas = execute_query(query, fetch=True)
        
        selected_id = st.selectbox("Selecione a empresa", empresas['idEmpresaPromotora'], format_func=lambda x: empresas[empresas['idEmpresaPromotora'] == x]['nomeEmpresaPromotora'].values[0])
        
        query = "SELECT nomeEmpresaPromotora, siglaEmpresaPromotora FROM EmpresaPromotora WHERE idEmpresaPromotora = ?"
        empresa = execute_query(query, (selected_id,), fetch=True).iloc[0]
        
        nome = st.text_input("Nome", value=empresa['nomeEmpresaPromotora'])
        sigla = st.text_input("Sigla", value=empresa['siglaEmpresaPromotora'], max_chars=10)
        
        if st.button("Atualizar"):
            query = "UPDATE EmpresaPromotora SET nomeEmpresaPromotora = ?, siglaEmpresaPromotora = ? WHERE idEmpresaPromotora = ?"
            if execute_query(query, (nome, sigla, selected_id)):
                st.success("Empresa atualizada com sucesso!")
    
    elif operation == "Deletar":
        st.subheader("Deletar Empresa Promotora")
        query = "SELECT idEmpresaPromotora, nomeEmpresaPromotora FROM EmpresaPromotora"
        empresas = execute_query(query, fetch=True)
        
        selected_id = st.selectbox("Selecione a empresa para deletar", empresas['idEmpresaPromotora'], format_func=lambda x: empresas[empresas['idEmpresaPromotora'] == x]['nomeEmpresaPromotora'].values[0])
        
        if st.button("Confirmar Exclusão"):
            # Verificar se há programas associados
            query_check = "SELECT COUNT(*) FROM Programa WHERE idEmpresaPromotoraPrograma = ?"
            count = execute_query(query_check, (selected_id,), fetch=True).iloc[0, 0]
            
            if count > 0:
                st.error("Não é possível deletar esta empresa porque existem programas associados a ela.")
            else:
                query = "DELETE FROM EmpresaPromotora WHERE idEmpresaPromotora = ?"
                if execute_query(query, (selected_id,)):
                    st.success("Empresa deletada com sucesso!")

def programa_page():
    st.title("Gestão de Programas")
    
    operation = st.radio("Operação", ["Criar", "Ler", "Atualizar", "Deletar"])
    
    if operation == "Criar":
        st.subheader("Adicionar Novo Programa")
        
        # Obter lista de empresas promotoras
        empresas = execute_query("SELECT idEmpresaPromotora, nomeEmpresaPromotora FROM EmpresaPromotora", fetch=True)
        empresa_options = {row['idEmpresaPromotora']: row['nomeEmpresaPromotora'] for _, row in empresas.iterrows()}
        
        nome = st.text_input("Nome do Programa")
        empresa_id = st.selectbox("Empresa Promotora", options=list(empresa_options.keys()), format_func=lambda x: empresa_options[x])
        
        if st.button("Salvar"):
            query = "INSERT INTO Programa (nomePrograma, idEmpresaPromotoraPrograma) VALUES (?, ?)"
            if execute_query(query, (nome, empresa_id)):
                st.success("Programa adicionado com sucesso!")
    
    elif operation == "Ler":
        st.subheader("Lista de Programas")
        query = """
        SELECT p.idPrograma, p.nomePrograma, e.nomeEmpresaPromotora 
        FROM Programa p
        JOIN EmpresaPromotora e ON p.idEmpresaPromotoraPrograma = e.idEmpresaPromotora
        """
        df = execute_query(query, fetch=True)
        st.dataframe(df)
    
    elif operation == "Atualizar":
        st.subheader("Atualizar Programa")
        
        # Obter lista de programas
        programas = execute_query("SELECT idPrograma, nomePrograma FROM Programa", fetch=True)
        selected_id = st.selectbox("Selecione o programa", programas['idPrograma'], format_func=lambda x: programas[programas['idPrograma'] == x]['nomePrograma'].values[0])
        
        # Obter dados atuais
        query = """
        SELECT nomePrograma, idEmpresaPromotoraPrograma 
        FROM Programa 
        WHERE idPrograma = ?
        """
        programa = execute_query(query, (selected_id,), fetch=True).iloc[0]
        
        # Obter lista de empresas promotoras
        empresas = execute_query("SELECT idEmpresaPromotora, nomeEmpresaPromotora FROM EmpresaPromotora", fetch=True)
        empresa_options = {row['idEmpresaPromotora']: row['nomeEmpresaPromotora'] for _, row in empresas.iterrows()}
        
        nome = st.text_input("Nome", value=programa['nomePrograma'])
        empresa_id = st.selectbox("Empresa Promotora", 
                                options=list(empresa_options.keys()), 
                                index=list(empresa_options.keys()).index(programa['idEmpresaPromotoraPrograma']),
                                format_func=lambda x: empresa_options[x])
        
        if st.button("Atualizar"):
            query = "UPDATE Programa SET nomePrograma = ?, idEmpresaPromotoraPrograma = ? WHERE idPrograma = ?"
            if execute_query(query, (nome, empresa_id, selected_id)):
                st.success("Programa atualizado com sucesso!")
    
    elif operation == "Deletar":
        st.subheader("Deletar Programa")
        
        programas = execute_query("SELECT idPrograma, nomePrograma FROM Programa", fetch=True)
        selected_id = st.selectbox("Selecione o programa para deletar", programas['idPrograma'], format_func=lambda x: programas[programas['idPrograma'] == x]['nomePrograma'].values[0])
        
        if st.button("Confirmar Exclusão"):
            query = "DELETE FROM Programa WHERE idPrograma = ?"
            if execute_query(query, (selected_id,)):
                st.success("Programa deletado com sucesso!")

# Funções similares para as outras tabelas (CategoriaServico, TipoServico, Instrumento, Modalidade, PorteEmpresarial, Setor, MacroSegmento)
# Implementação similar às funções acima, adaptando para cada tabela específica

def categoria_servico_page():
    st.title("Gestão de Categorias de Serviço")
    crud_simple_table("CategoriaServico", "idCategoriaServico", "nomeCategoriaServico", "Categoria de Serviço")

def tipo_servico_page():
    st.title("Gestão de Tipos de Serviço")
    crud_simple_table("TipoServico", "idTipoServico", "nomeTipoServico", "Tipo de Serviço")

def instrumento_page():
    st.title("Gestão de Instrumentos")
    crud_simple_table("Instrumento", "idInstrumento", "nomeInstrumento", "Instrumento")

def modalidade_page():
    st.title("Gestão de Modalidades")
    crud_simple_table("Modalidade", "idModalidade", "nomeModalidade", "Modalidade")

def porte_empresarial_page():
    st.title("Gestão de Portes Empresariais")
    
    operation = st.radio("Operação", ["Criar", "Ler", "Atualizar", "Deletar"])
    
    if operation == "Criar":
        st.subheader("Adicionar Novo Porte Empresarial")
        nome = st.text_input("Nome do Porte Empresarial")
        sigla = st.text_input("Sigla", max_chars=15)
        
        if st.button("Salvar"):
            query = "INSERT INTO PorteEmpresarial (nomePorteEmpresarial, siglaPorteEmpresarial) VALUES (?, ?)"
            if execute_query(query, (nome, sigla)):
                st.success("Porte Empresarial adicionado com sucesso!")
    
    elif operation == "Ler":
        st.subheader("Lista de Portes Empresariais")
        query = "SELECT idPorteEmpresarial, nomePorteEmpresarial, siglaPorteEmpresarial FROM PorteEmpresarial"
        df = execute_query(query, fetch=True)
        st.dataframe(df)
    
    elif operation == "Atualizar":
        st.subheader("Atualizar Porte Empresarial")
        query = "SELECT idPorteEmpresarial, nomePorteEmpresarial, siglaPorteEmpresarial FROM PorteEmpresarial"
        portes = execute_query(query, fetch=True)
        
        selected_id = st.selectbox("Selecione o porte", portes['idPorteEmpresarial'], 
                                 format_func=lambda x: f"{portes[portes['idPorteEmpresarial'] == x]['nomePorteEmpresarial'].values[0]} ({portes[portes['idPorteEmpresarial'] == x]['siglaPorteEmpresarial'].values[0]})")
        
        porte = portes[portes['idPorteEmpresarial'] == selected_id].iloc[0]
        
        nome = st.text_input("Nome", value=porte['nomePorteEmpresarial'])
        sigla = st.text_input("Sigla", value=porte['siglaPorteEmpresarial'], max_chars=15)
        
        if st.button("Atualizar"):
            query = "UPDATE PorteEmpresarial SET nomePorteEmpresarial = ?, siglaPorteEmpresarial = ? WHERE idPorteEmpresarial = ?"
            if execute_query(query, (nome, sigla, selected_id)):
                st.success("Porte Empresarial atualizado com sucesso!")
    
    elif operation == "Deletar":
        st.subheader("Deletar Porte Empresarial")
        query = "SELECT idPorteEmpresarial, nomePorteEmpresarial, siglaPorteEmpresarial FROM PorteEmpresarial"
        portes = execute_query(query, fetch=True)
        
        selected_id = st.selectbox("Selecione o porte para deletar", portes['idPorteEmpresarial'], 
                                 format_func=lambda x: f"{portes[portes['idPorteEmpresarial'] == x]['nomePorteEmpresarial'].values[0]} ({portes[portes['idPorteEmpresarial'] == x]['siglaPorteEmpresarial'].values[0]})")
        
        if st.button("Confirmar Exclusão"):
            # Verificar se há público alvo associado
            query_check = "SELECT COUNT(*) FROM PublicoAlvo WHERE idPorteEmpresarialPublicoAlvo = ?"
            count = execute_query(query_check, (selected_id,), fetch=True).iloc[0, 0]
            
            if count > 0:
                st.error("Não é possível deletar este porte porque existem fichas técnicas associadas a ele.")
            else:
                query = "DELETE FROM PorteEmpresarial WHERE idPorteEmpresarial = ?"
                if execute_query(query, (selected_id,)):
                    st.success("Porte Empresarial deletado com sucesso!")

def setor_page():
    st.title("Gestão de Setores")
    crud_simple_table("Setor", "idSetor", "nomeSetor", "Setor")

def macro_segmento_page():
    st.title("Gestão de Macro Segmentos")
    crud_simple_table("MacroSegmento", "idMacroSegmento", "nomeMacroSegmento", "Macro Segmento")

# Função auxiliar para tabelas simples (apenas ID e Nome)
def crud_simple_table(table_name, id_column, name_column, display_name):
    operation = st.radio("Operação", ["Criar", "Ler", "Atualizar", "Deletar"])
    
    if operation == "Criar":
        st.subheader(f"Adicionar Novo {display_name}")
        nome = st.text_input(f"Nome do {display_name}")
        
        if st.button("Salvar"):
            query = f"INSERT INTO {table_name} ({name_column}) VALUES (?)"
            if execute_query(query, (nome,)):
                st.success(f"{display_name} adicionado com sucesso!")
    
    elif operation == "Ler":
        st.subheader(f"Lista de {display_name}s")
        query = f"SELECT {id_column}, {name_column} FROM {table_name}"
        df = execute_query(query, fetch=True)
        st.dataframe(df)
    
    elif operation == "Atualizar":
        st.subheader(f"Atualizar {display_name}")
        query = f"SELECT {id_column}, {name_column} FROM {table_name}"
        items = execute_query(query, fetch=True)
        
        selected_id = st.selectbox(f"Selecione o {display_name.lower()}", items[id_column], 
                                  format_func=lambda x: items[items[id_column] == x][name_column].values[0])
        
        current_name = items[items[id_column] == selected_id][name_column].values[0]
        nome = st.text_input("Nome", value=current_name)
        
        if st.button("Atualizar"):
            query = f"UPDATE {table_name} SET {name_column} = ? WHERE {id_column} = ?"
            if execute_query(query, (nome, selected_id)):
                st.success(f"{display_name} atualizado com sucesso!")
    
    elif operation == "Deletar":
        st.subheader(f"Deletar {display_name}")
        query = f"SELECT {id_column}, {name_column} FROM {table_name}"
        items = execute_query(query, fetch=True)
        
        selected_id = st.selectbox(f"Selecione o {display_name.lower()} para deletar", items[id_column], 
                                  format_func=lambda x: items[items[id_column] == x][name_column].values[0])
        
        if st.button("Confirmar Exclusão"):
            # Verificar se há relações de chave estrangeira
            fk_tables = {
                "CategoriaServico": "FichaTecnica",
                "TipoServico": "FichaTecnica",
                "Instrumento": "FichaTecnica",
                "Modalidade": "FichaTecnica",
                "Setor": "SetorIndicado",
                "MacroSegmento": "MacroSegmentoFichaTecnica"
            }
            
            if table_name in fk_tables:
                fk_table = fk_tables[table_name]
                fk_column = f"id{table_name}{fk_table.replace(table_name, '')}"
                query_check = f"SELECT COUNT(*) FROM {fk_table} WHERE {fk_column} = ?"
                count = execute_query(query_check, (selected_id,), fetch=True).iloc[0, 0]
                
                if count > 0:
                    st.error(f"Não é possível deletar este {display_name.lower()} porque existem registros associados na tabela {fk_table}.")
                    return
            
            query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            if execute_query(query, (selected_id,)):
                st.success(f"{display_name} deletado com sucesso!")

def ficha_tecnica_page():
    st.title("Gestão de Fichas Técnicas")
    
    operation = st.radio("Operação", ["Criar", "Ler", "Atualizar", "Deletar", "Gerenciar Público Alvo", "Gerenciar Setores Indicados", "Gerenciar Macro Segmentos"])
    
    if operation == "Criar":
        st.subheader("Adicionar Nova Ficha Técnica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.text_input("Código", max_chars=15)
            nome = st.text_input("Nome", max_chars=150)
            tema = st.text_input("Tema", max_chars=50)
            sub_tema = st.text_input("Sub-tema", max_chars=50)
        
        with col2:
            # Obter opções para campos de chave estrangeira
            categorias = execute_query("SELECT idCategoriaServico, nomeCategoriaServico FROM CategoriaServico", fetch=True)
            categoria_id = st.selectbox("Categoria de Serviço", categorias['idCategoriaServico'], 
                                       format_func=lambda x: categorias[categorias['idCategoriaServico'] == x]['nomeCategoriaServico'].values[0])
            
            tipos = execute_query("SELECT idTipoServico, nomeTipoServico FROM TipoServico", fetch=True)
            tipo_id = st.selectbox("Tipo de Serviço", tipos['idTipoServico'], 
                                  format_func=lambda x: tipos[tipos['idTipoServico'] == x]['nomeTipoServico'].values[0])
            
            instrumentos = execute_query("SELECT idInstrumento, nomeInstrumento FROM Instrumento", fetch=True)
            instrumento_id = st.selectbox("Instrumento", instrumentos['idInstrumento'], 
                                         format_func=lambda x: instrumentos[instrumentos['idInstrumento'] == x]['nomeInstrumento'].values[0])
            
            modalidades = execute_query("SELECT idModalidade, nomeModalidade FROM Modalidade", fetch=True)
            modalidade_id = st.selectbox("Modalidade", modalidades['idModalidade'], 
                                        format_func=lambda x: modalidades[modalidades['idModalidade'] == x]['nomeModalidade'].values[0])
            
            carga_horaria = st.number_input("Carga Horária", min_value=0, step=1)
            link = st.text_input("Link", max_chars=250)
        
        if st.button("Salvar"):
            query = """
            INSERT INTO FichaTecnica (
                codigoFichaTecnica, nomeFichaTecnica, temaFichaTecnica, subTemaFichaTecnica,
                idCategoriaServicoFichaTecnica, idTipoServicoFichaTecnica, 
                idInstrumentoFichaTecnica, idModalidadeFichaTecnica, 
                cargaHorariaFichaTecnica, linkFichaTecnica
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                codigo, nome, tema, sub_tema,
                categoria_id, tipo_id, instrumento_id, modalidade_id,
                carga_horaria, link
            )
            
            if execute_query(query, params):
                st.success("Ficha Técnica adicionada com sucesso!")
    
    elif operation == "Ler":
        st.subheader("Lista de Fichas Técnicas")
        
        query = """
        SELECT 
            ft.idFichaTecnica, ft.codigoFichaTecnica, ft.nomeFichaTecnica,
            ft.temaFichaTecnica, ft.subTemaFichaTecnica,
            cs.nomeCategoriaServico, ts.nomeTipoServico,
            i.nomeInstrumento, m.nomeModalidade,
            ft.cargaHorariaFichaTecnica, ft.linkFichaTecnica
        FROM FichaTecnica ft
        JOIN CategoriaServico cs ON ft.idCategoriaServicoFichaTecnica = cs.idCategoriaServico
        JOIN TipoServico ts ON ft.idTipoServicoFichaTecnica = ts.idTipoServico
        JOIN Instrumento i ON ft.idInstrumentoFichaTecnica = i.idInstrumento
        JOIN Modalidade m ON ft.idModalidadeFichaTecnica = m.idModalidade
        """
        
        df = execute_query(query, fetch=True)
        st.dataframe(df)
    
    elif operation == "Atualizar":
        st.subheader("Atualizar Ficha Técnica")
        
        # Obter lista de fichas técnicas
        fichas = execute_query("SELECT idFichaTecnica, nomeFichaTecnica FROM FichaTecnica", fetch=True)
        selected_id = st.selectbox("Selecione a ficha técnica", fichas['idFichaTecnica'], 
                                  format_func=lambda x: fichas[fichas['idFichaTecnica'] == x]['nomeFichaTecnica'].values[0])
        
        # Obter dados atuais
        query = """
        SELECT 
            codigoFichaTecnica, nomeFichaTecnica, temaFichaTecnica, subTemaFichaTecnica,
            idCategoriaServicoFichaTecnica, idTipoServicoFichaTecnica, 
            idInstrumentoFichaTecnica, idModalidadeFichaTecnica, 
            cargaHorariaFichaTecnica, linkFichaTecnica
        FROM FichaTecnica
        WHERE idFichaTecnica = ?
        """
        ficha = execute_query(query, (selected_id,), fetch=True).iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.text_input("Código", value=ficha['codigoFichaTecnica'], max_chars=15)
            nome = st.text_input("Nome", value=ficha['nomeFichaTecnica'], max_chars=150)
            tema = st.text_input("Tema", value=ficha['temaFichaTecnica'], max_chars=50)
            sub_tema = st.text_input("Sub-tema", value=ficha['subTemaFichaTecnica'], max_chars=50)
        
        with col2:
            # Obter opções para campos de chave estrangeira
            categorias = execute_query("SELECT idCategoriaServico, nomeCategoriaServico FROM CategoriaServico", fetch=True)
            categoria_id = st.selectbox("Categoria de Serviço", categorias['idCategoriaServico'], 
                                      index=categorias[categorias['idCategoriaServico'] == ficha['idCategoriaServicoFichaTecnica']].index[0],
                                      format_func=lambda x: categorias[categorias['idCategoriaServico'] == x]['nomeCategoriaServico'].values[0])
            
            tipos = execute_query("SELECT idTipoServico, nomeTipoServico FROM TipoServico", fetch=True)
            tipo_id = st.selectbox("Tipo de Serviço", tipos['idTipoServico'], 
                                 index=tipos[tipos['idTipoServico'] == ficha['idTipoServicoFichaTecnica']].index[0],
                                 format_func=lambda x: tipos[tipos['idTipoServico'] == x]['nomeTipoServico'].values[0])
            
            instrumentos = execute_query("SELECT idInstrumento, nomeInstrumento FROM Instrumento", fetch=True)
            instrumento_id = st.selectbox("Instrumento", instrumentos['idInstrumento'], 
                                        index=instrumentos[instrumentos['idInstrumento'] == ficha['idInstrumentoFichaTecnica']].index[0],
                                        format_func=lambda x: instrumentos[instrumentos['idInstrumento'] == x]['nomeInstrumento'].values[0])
            
            modalidades = execute_query("SELECT idModalidade, nomeModalidade FROM Modalidade", fetch=True)
            modalidade_id = st.selectbox("Modalidade", modalidades['idModalidade'], 
                                       index=modalidades[modalidades['idModalidade'] == ficha['idModalidadeFichaTecnica']].index[0],
                                       format_func=lambda x: modalidades[modalidades['idModalidade'] == x]['nomeModalidade'].values[0])
            
            carga_horaria = st.number_input("Carga Horária", value=ficha['cargaHorariaFichaTecnica'], min_value=0, step=1)
            link = st.text_input("Link", value=ficha['linkFichaTecnica'], max_chars=250)
        
        if st.button("Atualizar"):
            query = """
            UPDATE FichaTecnica SET
                codigoFichaTecnica = ?, nomeFichaTecnica = ?, temaFichaTecnica = ?, subTemaFichaTecnica = ?,
                idCategoriaServicoFichaTecnica = ?, idTipoServicoFichaTecnica = ?, 
                idInstrumentoFichaTecnica = ?, idModalidadeFichaTecnica = ?, 
                cargaHorariaFichaTecnica = ?, linkFichaTecnica = ?
            WHERE idFichaTecnica = ?
            """
            params = (
                codigo, nome, tema, sub_tema,
                categoria_id, tipo_id, instrumento_id, modalidade_id,
                carga_horaria, link, selected_id
            )
            
            if execute_query(query, params):
                st.success("Ficha Técnica atualizada com sucesso!")
    
    elif operation == "Deletar":
        st.subheader("Deletar Ficha Técnica")
        
        fichas = execute_query("SELECT idFichaTecnica, nomeFichaTecnica FROM FichaTecnica", fetch=True)
        selected_id = st.selectbox("Selecione a ficha técnica para deletar", fichas['idFichaTecnica'], 
                                  format_func=lambda x: fichas[fichas['idFichaTecnica'] == x]['nomeFichaTecnica'].values[0])
        
        if st.button("Confirmar Exclusão"):
            # Verificar relações em tabelas associativas
            tables_to_check = ["PublicoAlvo", "SetorIndicado", "MacroSegmentoFichaTecnica"]
            has_relations = False
            
            for table in tables_to_check:
                query_check = f"SELECT COUNT(*) FROM {table} WHERE idFichaTecnica{table.replace('FichaTecnica', '')} = ?"
                count = execute_query(query_check, (selected_id,), fetch=True).iloc[0, 0]
                
                if count > 0:
                    has_relations = True
                    st.error(f"Não é possível deletar esta ficha técnica porque existem registros associados na tabela {table}.")
                    break
            
            if not has_relations:
                query = "DELETE FROM FichaTecnica WHERE idFichaTecnica = ?"
                if execute_query(query, (selected_id,)):
                    st.success("Ficha Técnica deletada com sucesso!")
    
    elif operation == "Gerenciar Público Alvo":
        st.subheader("Gerenciar Público Alvo das Fichas Técnicas")
        
        # Selecionar ficha técnica
        fichas = execute_query("SELECT idFichaTecnica, nomeFichaTecnica FROM FichaTecnica", fetch=True)
        selected_id = st.selectbox("Selecione a ficha técnica", fichas['idFichaTecnica'], 
                                  format_func=lambda x: fichas[fichas['idFichaTecnica'] == x]['nomeFichaTecnica'].values[0],
                                  key="publico_ficha_select")
        
        # Obter portes empresariais atuais
        query = """
        SELECT pe.idPorteEmpresarial, pe.nomePorteEmpresarial, pe.siglaPorteEmpresarial
        FROM PublicoAlvo pa
        JOIN PorteEmpresarial pe ON pa.idPorteEmpresarialPublicoAlvo = pe.idPorteEmpresarial
        WHERE pa.idFichaTecnicaPublicoAlvo = ?
        """
        portes_atual = execute_query(query, (selected_id,), fetch=True)
        
        # Obter todos os portes empresariais
        portes_all = execute_query("SELECT idPorteEmpresarial, nomePorteEmpresarial, siglaPorteEmpresarial FROM PorteEmpresarial", fetch=True)
        
        # Converter para formato mais fácil de manipular
        portes_atual_ids = set(portes_atual['idPorteEmpresarial']) if not portes_atual.empty else set()
        portes_all_dict = {row['idPorteEmpresarial']: f"{row['nomePorteEmpresarial']} ({row['siglaPorteEmpresarial']})" 
                          for _, row in portes_all.iterrows()}
        
        # Widget multiselect para adicionar/remover portes
        selected_portes = st.multiselect(
            "Portes Empresariais",
            options=portes_all_dict.keys(),
            default=list(portes_atual_ids),
            format_func=lambda x: portes_all_dict[x]
        )
        
        if st.button("Atualizar Público Alvo"):
            # Primeiro, remover portes que foram desmarcados
            to_remove = portes_atual_ids - set(selected_portes)
            for porte_id in to_remove:
                execute_query("DELETE FROM PublicoAlvo WHERE idFichaTecnicaPublicoAlvo = ? AND idPorteEmpresarialPublicoAlvo = ?", 
                            (selected_id, porte_id))
            
            # Depois, adicionar novos portes
            to_add = set(selected_portes) - portes_atual_ids
            for porte_id in to_add:
                execute_query("INSERT INTO PublicoAlvo (idFichaTecnicaPublicoAlvo, idPorteEmpresarialPublicoAlvo) VALUES (?, ?)", 
                             (selected_id, porte_id))
            
            st.success("Público alvo atualizado com sucesso!")
    
    elif operation == "Gerenciar Setores Indicados":
        st.subheader("Gerenciar Setores Indicados das Fichas Técnicas")
        
        # Selecionar ficha técnica
        fichas = execute_query("SELECT idFichaTecnica, nomeFichaTecnica FROM FichaTecnica", fetch=True)
        selected_id = st.selectbox("Selecione a ficha técnica", fichas['idFichaTecnica'], 
                                  format_func=lambda x: fichas[fichas['idFichaTecnica'] == x]['nomeFichaTecnica'].values[0],
                                  key="setor_ficha_select")
        
        # Obter setores atuais
        query = """
        SELECT s.idSetor, s.nomeSetor
        FROM SetorIndicado si
        JOIN Setor s ON si.idSetorSetorIndicado = s.idSetor
        WHERE si.idFichaTecnicaSetorIndicado = ?
        """
        setores_atual = execute_query(query, (selected_id,), fetch=True)
        
        # Obter todos os setores
        setores_all = execute_query("SELECT idSetor, nomeSetor FROM Setor", fetch=True)
        
        # Converter para formato mais fácil de manipular
        setores_atual_ids = set(setores_atual['idSetor']) if not setores_atual.empty else set()
        setores_all_dict = {row['idSetor']: row['nomeSetor'] for _, row in setores_all.iterrows()}
        
        # Widget multiselect para adicionar/remover setores
        selected_setores = st.multiselect(
            "Setores Indicados",
            options=setores_all_dict.keys(),
            default=list(setores_atual_ids),
            format_func=lambda x: setores_all_dict[x]
        )
        
        if st.button("Atualizar Setores Indicados"):
            # Primeiro, remover setores que foram desmarcados
            to_remove = setores_atual_ids - set(selected_setores)
            for setor_id in to_remove:
                execute_query("DELETE FROM SetorIndicado WHERE idFichaTecnicaSetorIndicado = ? AND idSetorSetorIndicado = ?", 
                            (selected_id, setor_id))
            
            # Depois, adicionar novos setores
            to_add = set(selected_setores) - setores_atual_ids
            for setor_id in to_add:
                execute_query("INSERT INTO SetorIndicado (idFichaTecnicaSetorIndicado, idSetorSetorIndicado) VALUES (?, ?)", 
                             (selected_id, setor_id))
            
            st.success("Setores indicados atualizados com sucesso!")
    
    elif operation == "Gerenciar Macro Segmentos":
        st.subheader("Gerenciar Macro Segmentos das Fichas Técnicas")
        
        # Selecionar ficha técnica
        fichas = execute_query("SELECT idFichaTecnica, nomeFichaTecnica FROM FichaTecnica", fetch=True)
        selected_id = st.selectbox("Selecione a ficha técnica", fichas['idFichaTecnica'], 
                                  format_func=lambda x: fichas[fichas['idFichaTecnica'] == x]['nomeFichaTecnica'].values[0],
                                  key="macro_ficha_select")
        
        # Obter macro segmentos atuais
        query = """
        SELECT ms.idMacroSegmento, ms.nomeMacroSegmento
        FROM MacroSegmentoFichaTecnica msft
        JOIN MacroSegmento ms ON msft.idMacroSegmentoMacroSegmentoFichaTecnica = ms.idMacroSegmento
        WHERE msft.idFichaTecnicaMacroSegmentoFichaTecnica = ?
        """
        macros_atual = execute_query(query, (selected_id,), fetch=True)
        
        # Obter todos os macro segmentos
        macros_all = execute_query("SELECT idMacroSegmento, nomeMacroSegmento FROM MacroSegmento", fetch=True)
        
        # Converter para formato mais fácil de manipular
        macros_atual_ids = set(macros_atual['idMacroSegmento']) if not macros_atual.empty else set()
        macros_all_dict = {row['idMacroSegmento']: row['nomeMacroSegmento'] for _, row in macros_all.iterrows()}
        
        # Widget multiselect para adicionar/remover macro segmentos
        selected_macros = st.multiselect(
            "Macro Segmentos",
            options=macros_all_dict.keys(),
            default=list(macros_atual_ids),
            format_func=lambda x: macros_all_dict[x]
        )
        
        if st.button("Atualizar Macro Segmentos"):
            # Primeiro, remover macros que foram desmarcados
            to_remove = macros_atual_ids - set(selected_macros)
            for macro_id in to_remove:
                execute_query("DELETE FROM MacroSegmentoFichaTecnica WHERE idFichaTecnicaMacroSegmentoFichaTecnica = ? AND idMacroSegmentoMacroSegmentoFichaTecnica = ?", 
                             (selected_id, macro_id))
            
            # Depois, adicionar novos macros
            to_add = set(selected_macros) - macros_atual_ids
            for macro_id in to_add:
                execute_query("INSERT INTO MacroSegmentoFichaTecnica (idFichaTecnicaMacroSegmentoFichaTecnica, idMacroSegmentoMacroSegmentoFichaTecnica) VALUES (?, ?)", 
                             (selected_id, macro_id))
            
            st.success("Macro segmentos atualizados com sucesso!")

if __name__ == "__main__":
    main()