import streamlit as st
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bson import ObjectId
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
import re

def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10 % 11) % 10
    return cpf[-2:] == f"{dig1}{dig2}"

def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validar_telefone(telefone):
    return re.match(r"^\(?\d{2}\)?\s?\d{4,5}\-?\d{4}$", telefone)


# Carrega variáveis do .env
load_dotenv()

# Pega a URI do ambiente
uri = os.getenv("MONGO_URI")

# Função para conectar ao MongoDB
@st.cache_resource
def get_database_connection():
    client = MongoClient(uri)
    return client["Varejo_Python"]

# Importar os módulos do sistema
# Assumindo que todas as classes estão no arquivo sistema_varejo.py
from sistema_varejo import GerenciadorProdutos, GestaoEstoque, Cliente, Vendas, Relatorios

# Configuração da página
st.set_page_config(
    page_title="ByteBurguer ERP",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Função para inicializar as classes do sistema
@st.cache_resource
def inicializar_sistema():
    gerenciador_produtos = GerenciadorProdutos()
    gerenciador_clientes = Cliente()
    gestor_estoque = GestaoEstoque(gerenciador_produtos)
    vendas = Vendas(gerenciador_produtos, gerenciador_clientes, gestor_estoque)
    relatorios = Relatorios()
    
    return {
        "produtos": gerenciador_produtos,
        "clientes": gerenciador_clientes,
        "estoque": gestor_estoque,
        "vendas": vendas,
        "relatorios": relatorios
    }

# Inicializar sistema
sistema = inicializar_sistema()
db = get_database_connection()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #3498db;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .success-message {
        color: #27ae60;
        font-weight: bold;
    }
    .error-message {
        color: #e74c3c;
        font-weight: bold;
    }
    .instruction-box {
        background-color: #f8f9fa;
        border-left: 5px solid #3498db;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .dashboard-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Barra lateral com menu de navegação
st.sidebar.title("Menu de Navegação")
menu_options = [
    "Dashboard",
    "Produtos",
    "Clientes",
    "Estoque",
    "Vendas",
    "Relatórios"
]
selected_menu = st.sidebar.selectbox("Selecione uma opção", menu_options)

# Informações do sistema na barra lateral
st.sidebar.markdown("---")
st.sidebar.subheader("Informações do Sistema")
st.sidebar.info(
    """
    **Sistema de Gerenciamento do ByteBurguer** 

    Versão: **1.0.0**

    Desenvolvido para **Leonardo**

    OBS: Em troca de um **PyBurguer**

    """
)

# Função para formatar mensagens de sucesso
def show_success(message):
    st.markdown(f"<p class='success-message'>{message}</p>", unsafe_allow_html=True)

# Função para formatar mensagens de erro
def show_error(message):
    st.markdown(f"<p class='error-message'>{message}</p>", unsafe_allow_html=True)

# Função para mostrar instruções
def show_instructions(instructions):
    st.markdown(f"<div class='instruction-box'>{instructions}</div>", unsafe_allow_html=True)

# Função para criar cards do dashboard
def dashboard_card(title, value, description=""):
    st.markdown(
        f"""
        <div class='dashboard-card'>
            <h3>{title}</h3>
            <h2>{value}</h2>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Título principal
st.markdown("<h1 class='main-header'>Sistema de Gerenciamento do ByteBurguer</h1>", unsafe_allow_html=True)
st.markdown("<h5 class='main-header'>Devs: Fabio lima | Guilherme Almeida | Renato Barros | Vitor Barbosa</h5>", unsafe_allow_html=True)

# =========== DASHBOARD ===========
if selected_menu == "Dashboard":
    st.markdown("<h2 class='section-header'>Dashboard</h2>", unsafe_allow_html=True)
    
    show_instructions("""
    Bem-vindo ao Dashboard! Aqui você pode visualizar um resumo das principais métricas do sistema.
    """)
    
    # Obter dados para o dashboard
    total_produtos = len(list(db["estoque_produtos"].find()))
    total_clientes = len(list(db["clientes"].find()))
    total_vendas = len(list(db["vendas"].find()))
    
    # Calcular valor total em estoque
    produtos = list(db["estoque_produtos"].find())
    valor_estoque = sum(p.get("qnt_estoque", 0) * p.get("preco", 0) for p in produtos)
    
    # Criar layout em colunas para os cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="Total de Produtos", value=total_produtos)
        st.metric(label="Total de Vendas", value=total_vendas)
    
    with col2:
        st.metric(label="Total de Clientes", value=total_clientes)
        st.metric(label="Valor em Estoque", value=f"R$ {valor_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Gráfico de produtos por categoria
    st.subheader("Produtos por Categoria")
    
    # Contar produtos por categoria
    categorias = {}
    for p in produtos:
        categoria = p.get("categoria", "Sem categoria")
        categorias[categoria] = categorias.get(categoria, 0) + 1
    
    # Criar DataFrame para o gráfico
    df_categorias = pd.DataFrame({
        "Categoria": list(categorias.keys()),
        "Quantidade": list(categorias.values())
    })
    
    if not df_categorias.empty:
        # Gráfico melhorado de pizza com valores e porcentagens
        fig = px.pie(
            df_categorias, 
            values="Quantidade", 
            names="Categoria",
            color_discrete_sequence=px.colors.qualitative.Bold,
            hole=0.4,  # Donut chart
            title="Distribuição de Produtos por Categoria"
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label+value',
            hoverinfo='label+percent+value'
        )
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            margin=dict(t=60, b=60, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não há produtos cadastrados para exibir no gráfico.")
    
    # Gráfico de produtos com estoque baixo
    st.subheader("Produtos com Estoque Baixo")
    produtos_baixo_estoque = [p for p in produtos if p.get("qnt_estoque", 0) < 20]
    
    if produtos_baixo_estoque:
        df_baixo_estoque = pd.DataFrame([
            {
                "Produto": p.get("nome", ""),
                "Código": p.get("cod_produto", ""),
                "Estoque": p.get("qnt_estoque", 0),
                "Nível de Alerta": "Crítico" if p.get("qnt_estoque", 0) < 5 else "Baixo"
            }
            for p in produtos_baixo_estoque
        ])
        
        # Gráfico de barras horizontais com cores
        fig = px.bar(
            df_baixo_estoque.sort_values("Estoque"), 
            y="Produto",
            x="Estoque",
            color="Nível de Alerta",
            color_discrete_map={"Crítico": "#FF4136", "Baixo": "#FFDC00"},
            title="Produtos com Estoque Baixo",
            orientation='h',
            text="Estoque"
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="Quantidade em Estoque",
            yaxis_title="",
            legend_title="Nível de Alerta",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            margin=dict(l=20, r=20, t=60, b=60)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela complementar
        st.dataframe(df_baixo_estoque.sort_values("Estoque"), use_container_width=True)
    else:
        st.info("Não há produtos com estoque baixo.")
    
    # Adicionar um novo gráfico de valor em estoque por categoria
    st.subheader("Valor em Estoque por Categoria")
    
    # Calcular valor em estoque por categoria
    valor_por_categoria = {}
    for p in produtos:
        categoria = p.get("categoria", "Sem categoria")
        valor = p.get("qnt_estoque", 0) * p.get("preco", 0)
        valor_por_categoria[categoria] = valor_por_categoria.get(categoria, 0) + valor
    
    df_valor_categoria = pd.DataFrame({
        "Categoria": list(valor_por_categoria.keys()),
        "Valor": list(valor_por_categoria.values())
    })
    
    if not df_valor_categoria.empty:
        fig = px.bar(
            df_valor_categoria.sort_values("Valor", ascending=False),
            x="Categoria",
            y="Valor",
            color="Categoria",
            title="Valor Total em Estoque por Categoria",
            text_auto='.2s'
        )
        fig.update_layout(
            xaxis_title="Categoria",
            yaxis_title="Valor em Estoque (R$)",
            yaxis=dict(tickprefix="R$ "),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não há produtos cadastrados para exibir no gráfico.")

# =========== PRODUTOS ===========
elif selected_menu == "Produtos":
    st.markdown("<h2 class='section-header'>Gestão de Produtos</h2>", unsafe_allow_html=True)
    
    # Submenu para Produtos
    produto_submenu = st.radio(
        "Selecione a operação",
        ["Cadastrar Produto", "Listar Produtos", "Buscar Produto"]
    )
    
    if produto_submenu == "Cadastrar Produto":
        st.subheader("Cadastrar Novo Produto")
        
        show_instructions("""
        Preencha todos os campos abaixo para cadastrar um novo produto.
        Os campos com ( * ) são obrigatórios.
        """)
        
        with st.form("cadastro_produto_form"):
            nome = st.text_input("Nome do Produto *")
            cod_produto = st.text_input("Código do Produto *")
            categoria = st.selectbox(
                "Categoria",
                ["Eletrônicos", "Vestuário", "Alimentos", "Bebidas", "Utensílios", "Outros"]
            )
            qnt_estoque = st.number_input("Quantidade em Estoque", min_value=0, value=0)
            preco = st.number_input("Preço (R$)", min_value=0.0, step=0.01, format="%.2f")
            descricao = st.text_area("Descrição do Produto")
            fornecedor = st.text_input("Fornecedor")
            
            submit_button = st.form_submit_button("Cadastrar Produto")
            
        if submit_button:
            if not nome or not cod_produto:
                show_error("Nome e código do produto são obrigatórios.")
            else:
                try:
                    produto = sistema["produtos"].cadastrar_produto(
                        nome, cod_produto, categoria, qnt_estoque, preco, descricao, fornecedor
                    )
                    show_success(f"Produto '{nome}' cadastrado com sucesso!")
                    st.json(produto)
                except ValueError as e:
                    show_error(f"Erro ao cadastrar produto: {str(e)}")
    
    elif produto_submenu == "Listar Produtos":
        st.subheader("Lista de Produtos")
        
        show_instructions("""
        Aqui você pode visualizar todos os produtos cadastrados no sistema.
        Use o filtro para encontrar produtos específicos.
        """)
        
        # Buscar produtos do banco
        produtos = sistema["produtos"].obter_todos_produtos()
        
        # Opções de filtro
        filtro = st.text_input("Filtrar por nome ou código:")
        
        if produtos:
            # Converter para DataFrame
            df_produtos = pd.DataFrame([
                {
                    "Nome": p.get("nome", ""),
                    "Código": p.get("cod_produto", ""),
                    "Categoria": p.get("categoria", ""),
                    "Estoque": p.get("qnt_estoque", 0),
                    "Preço": f"R$ {p.get('preco', 0):.2f}",
                    "Fornecedor": p.get("fornecedor", "")
                }
                for p in produtos
            ])
            
            # Aplicar filtro se existir
            if filtro:
                df_filtrado = df_produtos[
                    df_produtos["Nome"].str.contains(filtro, case=False) | 
                    df_produtos["Código"].str.contains(filtro, case=False)
                ]
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.dataframe(df_produtos, use_container_width=True)
            
            # Gráfico de estoque por produto
            st.subheader("Estoque por Produto")
            fig = px.bar(df_produtos, x="Nome", y="Estoque", color="Categoria")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há produtos cadastrados no sistema.")
    
    elif produto_submenu == "Buscar Produto":
        st.subheader("Buscar Produto")
        
        show_instructions("""
        Digite o código do produto para buscar informações detalhadas.
        """)
        
        cod_produto = st.text_input("Código do Produto")
        
        if st.button("Buscar"):
            if not cod_produto:
                show_error("Por favor, informe o código do produto.")
            else:
                produto = sistema["produtos"].obter_produto(cod_produto)
                
                if produto:
                    st.subheader(produto.get("nome", ""))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Código:** {produto.get('cod_produto', '')}")
                        st.markdown(f"**Categoria:** {produto.get('categoria', '')}")
                        st.markdown(f"**Fornecedor:** {produto.get('fornecedor', '')}")
                    
                    with col2:
                        st.markdown(f"**Estoque:** {produto.get('qnt_estoque', 0)} unidades")
                        st.markdown(f"**Preço:** R$ {produto.get('preco', 0):.2f}")
                    
                    st.markdown("**Descrição:**")
                    st.markdown(produto.get("descricao", "Sem descrição"))
                    
                    # Mostrar alerta se estoque baixo
                    if produto.get("qnt_estoque", 0) < 20:
                        st.warning(f"⚠️ ALERTA: Estoque baixo ({produto.get('qnt_estoque', 0)} unidades)")
                else:
                    st.warning(f"Produto com código '{cod_produto}' não encontrado.")

# =========== CLIENTES ===========
elif selected_menu == "Clientes":
    st.markdown("<h2 class='section-header'>Gestão de Clientes</h2>", unsafe_allow_html=True)

    # Submenu para Clientes
    cliente_submenu = st.radio(
        "Selecione a operação",
        ["Cadastrar Cliente", "Listar Clientes", "Buscar Cliente"]
    )

    if cliente_submenu == "Cadastrar Cliente":
        st.subheader("Cadastrar Novo Cliente")

        show_instructions("""
        Preencha todos os campos abaixo para cadastrar um novo cliente.
        Os campos com ( * ) são obrigatórios.
        """)

        with st.form("cadastro_cliente_form"):
            nome = st.text_input("Nome do Cliente *")
            cpf = st.text_input("CPF *")
            email = st.text_input("E-mail *")
            telefone = st.text_input("Telefone *")

            submit_button = st.form_submit_button("Cadastrar Cliente")

            if submit_button:
                if not nome.strip() or not cpf.strip() or not email.strip() or not telefone.strip():
                    show_error("Todos os campos são obrigatórios.")
                elif not cpf.isdigit():
                    show_error("O CPF deve conter apenas números.")
                elif not validar_cpf(cpf):
                    show_error("CPF inválido.")
                elif not validar_email(email):
                    show_error("E-mail inválido.")
                elif not validar_telefone(telefone):
                    show_error("Telefone inválido. Exemplo: (11) 91234-5678")
                else:
                    try:
                        cliente = sistema["clientes"].cadastro(nome, cpf, email, telefone)
                        show_success(f"Cliente '{nome}' cadastrado com sucesso!")
                        st.json(cliente)
                    except ValueError as e:
                        show_error(f"Erro ao cadastrar cliente: {str(e)}")

    elif cliente_submenu == "Listar Clientes":
        st.subheader("Lista de Clientes")

        show_instructions("""
        Aqui você pode visualizar todos os clientes cadastrados no sistema.
        Use o filtro para encontrar clientes específicos.
        """)

        # Buscar clientes do banco
        clientes = sistema["clientes"].obter_todos_clientes()

        # Opções de filtro
        filtro = st.text_input("Filtrar por nome ou CPF:")

        if clientes:
            # Converter para DataFrame
            df_clientes = pd.DataFrame([
                {
                    "Nome": c.get("nome", ""),
                    "CPF": c.get("cpf", ""),
                    "E-mail": c.get("email", ""),
                    "Telefone": c.get("telefone", "")
                }
                for c in clientes
            ])

            # Aplicar filtro se existir
            if filtro:
                df_filtrado = df_clientes[
                    df_clientes["Nome"].str.contains(filtro, case=False) |
                    df_clientes["CPF"].str.contains(filtro, case=False)
                ]
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.dataframe(df_clientes, use_container_width=True)
        else:
            st.info("Não há clientes cadastrados no sistema.")

    elif cliente_submenu == "Buscar Cliente":
        st.subheader("Buscar Cliente")

        show_instructions("""
        Digite o CPF do cliente para buscar informações detalhadas.
        """)

        cpf = st.text_input("CPF do Cliente")

        if st.button("Buscar"):
            if not cpf:
                show_error("Por favor, informe o CPF do cliente.")
            else:
                cliente = sistema["clientes"].obter_cliente(cpf)

                if cliente:
                    st.subheader(cliente.get("nome", ""))

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**CPF:** {cliente.get('cpf', '')}")
                        st.markdown(f"**E-mail:** {cliente.get('email', '')}")

                    with col2:
                        st.markdown(f"**Telefone:** {cliente.get('telefone', '')}")

                    # Buscar histórico de compras
                    vendas_cliente = sistema["vendas"].obter_venda_por_cliente(cpf)

                    if vendas_cliente:
                        st.subheader("Histórico de Compras")

                        # Converter para DataFrame
                        df_vendas = pd.DataFrame([
                            {
                                "Data": v.get("data_venda", "").strftime("%d/%m/%Y %H:%M"),
                                "Produto": sistema["produtos"].obter_produto(v.get("cod_produto", "")).get("nome", ""),
                                "Quantidade": v.get("qnt_vendida", 0),
                                "Valor Total": f"R$ {v.get('valor_total', 0):.2f}"
                            }
                            for v in vendas_cliente
                        ])

                        st.dataframe(df_vendas, use_container_width=True)

                        # Gráfico de compras por mês
                        st.subheader("Compras por Mês")

                        # Preparar dados para o gráfico
                        for v in vendas_cliente:
                            v["mes"] = v.get("data_venda", "").strftime("%Y-%m")

                        compras_por_mes = {}
                        for v in vendas_cliente:
                            mes = v.get("mes", "")
                            compras_por_mes[mes] = compras_por_mes.get(mes, 0) + v.get("valor_total", 0)

                        df_compras_mes = pd.DataFrame({
                            "Mês": list(compras_por_mes.keys()),
                            "Valor Total": list(compras_por_mes.values())
                        })

                        fig = px.line(df_compras_mes, x="Mês", y="Valor Total", markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Este cliente ainda não realizou compras.")
                else:
                    st.warning(f"Cliente com CPF '{cpf}' não encontrado.")

# =========== ESTOQUE ===========
elif selected_menu == "Estoque":
    st.markdown("<h2 class='section-header'>Gestão de Estoque</h2>", unsafe_allow_html=True)

    # Submenu para Estoque
    estoque_submenu = st.radio(
        "Selecione a operação",
        ["Adicionar Estoque", "Remover Estoque", "Ajustar Estoque", "Alerta de Estoque Baixo"]
    )

    if estoque_submenu == "Adicionar Estoque":
        st.subheader("Adicionar Estoque")

        show_instructions("""
        Informe o código do produto e a quantidade a ser adicionada ao estoque.
        """)

        with st.form("adicionar_estoque_form"):
            cod_produto = st.text_input("Código do Produto *")
            qnt_adicional = st.number_input("Quantidade a Adicionar", min_value=1, value=1)
            motivo = st.text_input("Motivo", value="Entrada padrão")

            submit_button = st.form_submit_button("Adicionar ao Estoque")

            if submit_button:
                if not cod_produto:
                    show_error("Por favor, informe o código do produto.")
                else:
                    try:
                        resultado = sistema["estoque"].adicionar_estoque(cod_produto, qnt_adicional, motivo)
                        show_success(resultado)

                        # Mostrar produto atualizado
                        produto = sistema["produtos"].obter_produto(cod_produto)
                        st.info(f"Estoque atual: {produto.get('qnt_estoque', 0)} unidades")
                    except ValueError as e:
                        show_error(f"Erro ao adicionar estoque: {str(e)}")

    elif estoque_submenu == "Remover Estoque":
        st.subheader("Remover Estoque")

        show_instructions("""
        Informe o código do produto e a quantidade a ser removida do estoque.
        """)

        with st.form("remover_estoque_form"):
            cod_produto = st.text_input("Código do Produto *")
            qnt_remover = st.number_input("Quantidade a Remover", min_value=1, value=1)
            motivo = st.text_input("Motivo", value="Saída padrão")

            submit_button = st.form_submit_button("Remover do Estoque")

            if submit_button:
                if not cod_produto:
                    show_error("Por favor, informe o código do produto.")
                else:
                    try:
                        resultado = sistema["estoque"].remover_estoque(cod_produto, qnt_remover, motivo)
                        show_success(resultado)

                        # Mostrar produto atualizado
                        produto = sistema["produtos"].obter_produto(cod_produto)
                        st.info(f"Estoque atual: {produto.get('qnt_estoque', 0)} unidades")
                    except ValueError as e:
                        show_error(f"Erro ao remover estoque: {str(e)}")

    elif estoque_submenu == "Ajustar Estoque":
        st.subheader("Ajustar Estoque")

        show_instructions("""
        Informe o código do produto e a nova quantidade em estoque.
        Use essa opção para corrigir discrepâncias no estoque.
        """)

        with st.form("ajustar_estoque_form"):
            cod_produto = st.text_input("Código do Produto *")

            # Se o produto for encontrado, mostrar o estoque atual
            if cod_produto:
                produto = sistema["produtos"].obter_produto(cod_produto)
                if produto:
                    estoque_atual = produto.get("qnt_estoque", 0)
                    qnt_atualizada = st.number_input("Nova Quantidade", min_value=0, value=estoque_atual)
                else:
                    qnt_atualizada = st.number_input("Nova Quantidade", min_value=0, value=0)
            else:
                qnt_atualizada = st.number_input("Nova Quantidade", min_value=0, value=0)

            motivo = st.text_input("Motivo", value="Ajuste de inventário")

            submit_button = st.form_submit_button("Ajustar Estoque")

            if submit_button:
                if not cod_produto:
                    show_error("Por favor, informe o código do produto.")
                else:
                    try:
                        resultado = sistema["estoque"].atualizacao_estoque(cod_produto, qnt_atualizada, motivo)
                        show_success(resultado)

                        # Mostrar produto atualizado
                        produto = sistema["produtos"].obter_produto(cod_produto)
                        st.info(f"Estoque atual: {produto.get('qnt_estoque', 0)} unidades")
                    except ValueError as e:
                        show_error(f"Erro ao ajustar estoque: {str(e)}")

    elif estoque_submenu == "Alerta de Estoque Baixo":
        st.subheader("Alerta de Estoque Baixo")

        show_instructions("""
        Aqui você pode visualizar produtos com estoque abaixo do mínimo recomendado.
        """)

        qnt_minimo = st.slider("Quantidade Mínima", min_value=1, max_value=100, value=20)

        if st.button("Verificar Estoque Baixo"):
            # Buscar produtos com estoque baixo
            produtos = sistema["produtos"].obter_todos_produtos()
            produtos_baixo_estoque = [p for p in produtos if p.get("qnt_estoque", 0) < qnt_minimo]

            if produtos_baixo_estoque:
                st.warning(f"⚠️ {len(produtos_baixo_estoque)} produtos com estoque abaixo do mínimo!")

                # Converter para DataFrame
                df_baixo_estoque = pd.DataFrame([
                    {
                        "Nome": p.get("nome", ""),
                        "Código": p.get("cod_produto", ""),
                        "Categoria": p.get("categoria", ""),
                        "Estoque Atual": p.get("qnt_estoque", 0),
                        "Mínimo Recomendado": qnt_minimo,
                        "Status": "CRÍTICO" if p.get("qnt_estoque", 0) < qnt_minimo * 0.5 else "BAIXO"
                    }
                    for p in produtos_baixo_estoque
                ])

                # Estilizar o DataFrame
                def highlight_status(val):
                    if val == "CRÍTICO":
                        return 'background-color: #ffcccc; color: #cc0000'
                    elif val == "BAIXO":
                        return 'background-color: #ffffcc; color: #666600'
                    else:
                        return ''

                st.dataframe(df_baixo_estoque.style.applymap(highlight_status, subset=['Status']), use_container_width=True)

                # Gráfico de estoque baixo
                fig = px.bar(
                    df_baixo_estoque,
                    x="Nome",
                    y="Estoque Atual",
                    color="Status",
                    color_discrete_map={"CRÍTICO": "#cc0000", "BAIXO": "#cccc00"},
                    title="Produtos com Estoque Baixo"
                )

                # Adicionar linha de estoque mínimo
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    x1=len(df_baixo_estoque)-0.5,
                    y0=qnt_minimo,
                    y1=qnt_minimo,
                    line=dict(color="red", width=2, dash="dash")
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("Não há produtos com estoque abaixo do mínimo.")


# =========== VENDAS ===========
elif selected_menu == "Vendas":
    st.markdown("<h2 class='section-header'>Gestão de Vendas</h2>", unsafe_allow_html=True)
        
    # Submenu para Vendas
    vendas_submenu = st.radio(
        "Selecione a operação",
        ["Registrar Venda", "Consultar Vendas", "Emitir Nota Fiscal"]
    )
    
    if vendas_submenu == "Registrar Venda":
        st.subheader("Registrar Nova Venda")
        
        show_instructions("""
        Preencha todos os campos para registrar uma venda.
        O sistema verifica automaticamente a disponibilidade de estoque.
        Você pode aplicar promoções e descontos antes de finalizar a venda.
        """)
        
        # Inicializar variáveis na session_state se não existirem
        if 'quantidade_venda' not in st.session_state:
            st.session_state.quantidade_venda = 1
        if 'desconto_ativo' not in st.session_state:
            st.session_state.desconto_ativo = False
        if 'promocao_ativa' not in st.session_state:
            st.session_state.promocao_ativa = False
        if 'valor_desconto' not in st.session_state:
            st.session_state.valor_desconto = 0.0
        if 'tipo_desconto' not in st.session_state:
            st.session_state.tipo_desconto = "Valor (R$)"
        if 'codigo_promocional' not in st.session_state:
            st.session_state.codigo_promocional = "PRIMEIRA_COMPRA"
            
        # Callbacks simplificados para evitar conflitos
        def toggle_desconto():
            st.session_state.desconto_ativo = not st.session_state.desconto_ativo
            if st.session_state.desconto_ativo:
                st.session_state.promocao_ativa = False
                
        def toggle_promocao():
            st.session_state.promocao_ativa = not st.session_state.promocao_ativa
            if st.session_state.promocao_ativa:
                st.session_state.desconto_ativo = False
        
        # Campo para selecionar o produto
        produtos = sistema["produtos"].obter_todos_produtos()
        opcoes_produtos = {p.get("cod_produto"): f"{p.get('nome')} (Código: {p.get('cod_produto')}, Estoque: {p.get('qnt_estoque')})" for p in produtos}
        
        cod_produto = st.selectbox(
            "Selecione o Produto *",
            options=list(opcoes_produtos.keys()),
            format_func=lambda x: opcoes_produtos.get(x, x)
        )
        
        # Campo para selecionar o cliente
        clientes = sistema["clientes"].obter_todos_clientes()
        opcoes_clientes = {c.get("cpf"): f"{c.get('nome')} (CPF: {c.get('cpf')})" for c in clientes}
        
        cpf_cliente = st.selectbox(
            "Selecione o Cliente *",
            options=list(opcoes_clientes.keys()),
            format_func=lambda x: opcoes_clientes.get(x, x)
        )
        
        # Quantidade a vender
        produto_selecionado = sistema["produtos"].obter_produto(cod_produto) if cod_produto else None
        estoque_disponivel = produto_selecionado.get("qnt_estoque", 0) if produto_selecionado else 0
        
        qnt_vendida = st.number_input(
            "Quantidade", 
            min_value=1, 
            max_value=estoque_disponivel, 
            value=1,
            key="quantidade_venda"
        )
        
        # Calcular valores baseados na quantidade e descontos
        if produto_selecionado:
            preco_unitario = produto_selecionado.get("preco", 0)
            valor_total_original = preco_unitario * qnt_vendida
            
            st.markdown("### Detalhes da Venda")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"Preço Unitário: R$ {preco_unitario:.2f}")
            
            # Adicionar opções de desconto/promoção
            st.subheader("Descontos e Promoções")
            
            discount_tabs = st.tabs(["Aplicar Desconto", "Usar Código Promocional"])
            
            # Variáveis para armazenar valores de desconto
            valor_final = valor_total_original
            desconto_aplicado = 0
            desconto_info = None
            
            with discount_tabs[0]:
                aplicar_desconto = st.checkbox("Aplicar desconto nesta venda", 
                                             value=st.session_state.desconto_ativo, on_change=toggle_desconto)
                
                desconto_tipo = st.radio(
                    "Tipo de Desconto",
                    ["Valor (R$)", "Percentual (%)"],
                    disabled=not aplicar_desconto,
                    index=0 if st.session_state.tipo_desconto == "Valor (R$)" else 1
                )
                
                if desconto_tipo == "Valor (R$)":
                    valor_desconto = st.number_input(
                        "Valor do Desconto (R$)",
                        min_value=0.0,
                        max_value=float(valor_total_original * 0.3),  # Limite de 30% do valor
                        step=1.0,
                        disabled=not aplicar_desconto,
                        value=st.session_state.valor_desconto if st.session_state.tipo_desconto == "Valor (R$)" else 0.0
                    )
                    
                    # Calcular desconto em valor
                    if aplicar_desconto:
                        desconto_aplicado = valor_desconto
                        valor_final = valor_total_original - desconto_aplicado
                        if valor_final < 0:
                            valor_final = 0
                else:  # Percentual
                    valor_desconto = st.number_input(
                        "Percentual de Desconto (%)",
                        min_value=0.0,
                        max_value=30.0,  # Limite de 30%
                        step=1.0,
                        disabled=not aplicar_desconto,
                        value=st.session_state.valor_desconto if st.session_state.tipo_desconto == "Percentual (%)" else 0.0
                    )
                    
                    # Calcular desconto percentual
                    if aplicar_desconto:
                        desconto_aplicado = valor_total_original * (valor_desconto / 100)
                        valor_final = valor_total_original - desconto_aplicado
            
            with discount_tabs[1]:
                aplicar_promocao = st.checkbox("Usar código promocional", 
                                            value=st.session_state.promocao_ativa, on_change=toggle_promocao)
                
                promocoes = {
                    "PRIMEIRA_COMPRA": "15% na primeira compra",
                    "CLIENTE_VIP": "R$ 50,00 de desconto VIP",
                    "BLACK_FRIDAY": "25% na Black Friday",
                    "FRETE_GRATIS": "R$ 20,00 de desconto no frete"
                }
                
                codigo_promocional = st.selectbox(
                    "Selecione o código promocional",
                    options=list(promocoes.keys()),
                    format_func=lambda x: f"{x} - {promocoes.get(x, '')}",
                    disabled=not aplicar_promocao,
                    index=list(promocoes.keys()).index(st.session_state.codigo_promocional) if st.session_state.codigo_promocional in promocoes else 0
                )
                
                # Calcular desconto promocional
                if aplicar_promocao:
                    if codigo_promocional == "PRIMEIRA_COMPRA":
                        desconto_aplicado = valor_total_original * 0.15
                    elif codigo_promocional == "CLIENTE_VIP":
                        desconto_aplicado = 50.0 if valor_total_original >= 50.0 else valor_total_original
                    elif codigo_promocional == "BLACK_FRIDAY":
                        desconto_aplicado = valor_total_original * 0.25
                    elif codigo_promocional == "FRETE_GRATIS":
                        desconto_aplicado = 20.0 if valor_total_original >= 20.0 else valor_total_original
                    
                    valor_final = valor_total_original - desconto_aplicado
            
            # Mostrar resumo atualizado com desconto (se aplicável) antes de submeter
            with col2:
                if aplicar_desconto or aplicar_promocao:
                    valor_total_formatado = f"R$ {valor_total_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    descontos_formatado = f"R$ {desconto_aplicado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    valor_final_formatado = f"R$ {valor_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                    st.info(f"Valor Total (Original): {valor_total_formatado}")
                    st.info(f"Descontos Aplicados: {descontos_formatado}")
                    st.success(f"Valor Final: {valor_final_formatado}")
                else:
                    st.info(f"Valor Total: R$ {valor_total_original:.2f}")
            
            # Botão para registrar a venda
            if st.button("Registrar Venda"):
                if not cod_produto or not cpf_cliente:
                    show_error("Por favor, selecione o produto e o cliente.")
                else:
                    try:
                        # Registrar a venda
                        venda = sistema["vendas"].registrar_venda(cod_produto, cpf_cliente, qnt_vendida)
                        
                        # Aplicar desconto/promoção se selecionado
                        if aplicar_desconto:
                            tipo_desc = "valor" if desconto_tipo == "Valor (R$)" else "porcentagem"
                            desconto_info = sistema["vendas"].descontos(
                                venda["_id"], 
                                valor_desconto, 
                                tipo_desconto=tipo_desc
                            )
                        elif aplicar_promocao:
                            desconto_info = sistema["vendas"].aplicar_promocao(
                                venda["_id"], 
                                codigo_promocional
                            )
                        
                        show_success("Venda registrada com sucesso!")
                        
                        # Mostrar detalhes da venda
                        st.subheader("Detalhes da Venda")
                        
                        produto = sistema["produtos"].obter_produto(cod_produto)
                        cliente = sistema["clientes"].obter_cliente(cpf_cliente)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Produto:** {produto.get('nome', '')}")
                            st.markdown(f"**Quantidade:** {qnt_vendida}")
                        
                        with col2:
                            st.markdown(f"**Cliente:** {cliente.get('nome', '')}")
                            st.markdown(f"**CPF:** {cpf_cliente}")
                            
                            # Mostrar valor com desconto se aplicado
                            if desconto_info:
                                st.markdown(f"**Valor Total (Original):** R$ {venda.get('valor_total', 0):.2f}")
                                st.markdown(f"**Desconto Aplicado:** R$ {desconto_info.get('desconto_aplicado', 0):.2f}")
                                st.markdown(f"**Valor Final:** R$ {desconto_info.get('valor_final', 0):.2f}")
                            else:
                                st.markdown(f"**Valor Total:** R$ {venda.get('valor_total', 0):.2f}")
                        
                        st.markdown(f"**Data da Venda:** {venda.get('data_venda', '').strftime('%d/%m/%Y %H:%M')}")
                        
                        # Opções para emitir nota fiscal
                        st.markdown("---")
                        
                        if st.button("Emitir Nota Fiscal"):
                            nota_fiscal = sistema["vendas"].emissao_nota_fiscal(venda.get("_id"), desconto=desconto_info)
                            st.code(nota_fiscal, language=None)
                            
                    except ValueError as e:
                        show_error(f"Erro ao registrar venda: {str(e)}")
        else:
            st.warning("Selecione um produto para continuar.")
    
    elif vendas_submenu == "Consultar Vendas":
        st.subheader("Consultar Vendas")
        
        show_instructions("""
        Use os filtros para consultar vendas realizadas.
        Você pode filtrar por data, cliente ou produto.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input(
                "Data Inicial", 
                value=dt.datetime.now() - dt.timedelta(days=30)
            )
        
        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=dt.datetime.now()
            )
        
        # Converter para datetime com hora
        data_inicio = dt.datetime.combine(data_inicio, dt.time.min)
        data_fim = dt.datetime.combine(data_fim, dt.time.max)
        
        # Opções para filtrar por cliente ou produto
        filtro_tipo = st.radio("Filtrar por:", ["Todos", "Cliente", "Produto"])
        
        if filtro_tipo == "Cliente":
            clientes = sistema["clientes"].obter_todos_clientes()
            opcoes_clientes = {c.get("cpf"): f"{c.get('nome')} (CPF: {c.get('cpf')})" for c in clientes}
            
            cpf_cliente = st.selectbox(
                "Selecione o Cliente",
                options=list(opcoes_clientes.keys()),
                format_func=lambda x: opcoes_clientes.get(x, x)
            )
        elif filtro_tipo == "Produto":
            produtos = sistema["produtos"].obter_todos_produtos()
            opcoes_produtos = {p.get("cod_produto"): f"{p.get('nome')} (Código: {p.get('cod_produto')})" for p in produtos}
            
            cod_produto = st.selectbox(
                "Selecione o Produto",
                options=list(opcoes_produtos.keys()),
                format_func=lambda x: opcoes_produtos.get(x, x)
            )
        
        if st.button("Consultar"):
            # Buscar vendas do banco conforme filtros
            if filtro_tipo == "Todos":
                vendas_filtradas = [v for v in sistema["vendas"].obter_todas_vendas() 
                                   if data_inicio <= v.get("data_venda", dt.datetime.min) <= data_fim]
            elif filtro_tipo == "Cliente":
                vendas_filtradas = [v for v in sistema["vendas"].obter_venda_por_cliente(cpf_cliente)
                                   if data_inicio <= v.get("data_venda", dt.datetime.min) <= data_fim]
            else:  # Produto
                vendas_filtradas = [v for v in sistema["vendas"].obter_todas_vendas()
                                   if v.get("cod_produto") == cod_produto and
                                   data_inicio <= v.get("data_venda", dt.datetime.min) <= data_fim]
            
            if vendas_filtradas:
                # Converter para DataFrame
                df_vendas = pd.DataFrame([
                    {
                        "Data": v.get("data_venda", "").strftime("%d/%m/%Y %H:%M"),
                        "Produto": db["estoque_produtos"].find_one({"cod_produto": v.get("cod_produto", "")}).get("nome", ""),
                        "Cliente": db["clientes"].find_one({"cpf": v.get("cpf_cliente", "")}).get("nome", ""),
                        "Quantidade": v.get("qnt_vendida", 0),
                        "Valor Total": v.get("valor_total", 0)
                    }
                    for v in vendas_filtradas
                ])
                
                # Exibir tabela
                df_vendas_display = df_vendas.copy()
                df_vendas_display["Valor Total"] = df_vendas_display["Valor Total"].apply(lambda x: f"R$ {x:.2f}")
                st.dataframe(df_vendas_display, use_container_width=True)
                
                # Resumo das vendas
                st.subheader("Resumo")
                
                qtd_vendas = len(df_vendas)
                valor_total = df_vendas["Valor Total"].sum()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Quantidade de Vendas", qtd_vendas)
                
                with col2:
                    st.metric("Valor Total", f"R$ {valor_total:.2f}")
                
                # Agrupar vendas por dia
                df_vendas["Data_Dia"] = pd.to_datetime(df_vendas["Data"]).dt.date
                vendas_por_dia = df_vendas.groupby("Data_Dia")["Valor Total"].sum().reset_index()
                
                fig = px.line(vendas_por_dia, x="Data_Dia", y="Valor Total", markers=True)
                fig.update_layout(yaxis_title="Valor Total (R$)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Adicionar área sob a curva
                fig.add_traces(
                    go.Scatter(
                        x=vendas_por_dia["Data_Dia"],
                        y=vendas_por_dia["Valor Total"],
                        mode="none",
                        fill="tozeroy",
                        fillcolor="rgba(73, 160, 181, 0.2)",
                        name="Área"
                    )
                )
                
                # Adicionar linha de média
                media_valor = vendas_por_dia["Valor Total"].mean()
                fig.add_shape(
                    type="line",
                    x0=vendas_por_dia["Data_Dia"].min(),
                    x1=vendas_por_dia["Data_Dia"].max(),
                    y0=media_valor,
                    y1=media_valor,
                    line=dict(color="red", width=2, dash="dash")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Adicionar estatísticas complementares
                media_diaria = vendas_por_dia["Valor Total"].mean()
                melhor_dia_idx = vendas_por_dia["Valor Total"].idxmax()
                melhor_dia = vendas_por_dia.iloc[melhor_dia_idx]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Média Diária", f"R$ {media_diaria:.2f}")
                with col2:
                    st.metric("Melhor Dia", f"{melhor_dia['Data_Dia'].strftime('%d/%m/%Y')} - R$ {melhor_dia['Valor Total']:.2f}")
            else:
                st.info("Nenhuma venda encontrada com os filtros selecionados.")
    
    elif vendas_submenu == "Emitir Nota Fiscal":
        st.subheader("Emitir Nota Fiscal")
        
        show_instructions("""
        Digite o ID da venda para emitir a nota fiscal.
        Você pode aplicar descontos opcionais antes de emitir a nota.
        """)
        
        id_venda = st.text_input("ID da Venda")
        
        if id_venda:
            try:
                venda = sistema["vendas"].obter_venda(id_venda)
                
                if venda:
                    # Mostrar detalhes da venda
                    produto = sistema["produtos"].obter_produto(venda.get("cod_produto", ""))
                    cliente = sistema["clientes"].obter_cliente(venda.get("cpf_cliente", ""))
                    
                    st.subheader("Detalhes da Venda")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Produto:** {produto.get('nome', '')}")
                        st.markdown(f"**Quantidade:** {venda.get('qnt_vendida', 0)}")
                    
                    with col2:
                        st.markdown(f"**Cliente:** {cliente.get('nome', '')}")
                        st.markdown(f"**Valor Total:** R$ {venda.get('valor_total', 0):.2f}")
                    
                    st.markdown(f"**Data da Venda:** {venda.get('data_venda', '').strftime('%d/%m/%Y %H:%M')}")
                    
                    # Opção para aplicar desconto
                    st.subheader("Aplicar Desconto (Opcional)")
                    
                    desconto_option = st.radio(
                        "Tipo de Desconto",
                        ["Sem Desconto", "Valor (R$)", "Percentual (%)", "Código Promocional"]
                    )
                    
                    desconto = None
                    
                    if desconto_option == "Valor (R$)":
                        valor_desconto = st.number_input(
                            "Valor do Desconto (R$)",
                            min_value=0.0,
                            max_value=float(venda.get("valor_total", 0) * 0.3),
                            step=0.01,
                            format="%.2f"
                        )
                        
                        if valor_desconto > 0:
                            desconto = sistema["vendas"].descontos(id_venda, valor_desconto, "valor")
                    
                    elif desconto_option == "Percentual (%)":
                        perc_desconto = st.number_input(
                            "Percentual de Desconto (%)",
                            min_value=0.0,
                            max_value=30.0,
                            step=0.1,
                            format="%.1f"
                        )
                        
                        if perc_desconto > 0:
                            desconto = sistema["vendas"].descontos(id_venda, perc_desconto, "porcentagem")
                    
                    elif desconto_option == "Código Promocional":
                        codigo_promocao = st.selectbox(
                            "Selecione o código promocional",
                            ["PRIMEIRA_COMPRA", "CLIENTE_VIP", "BLACK_FRIDAY", "FRETE_GRATIS"]
                        )
                        
                        desconto = sistema["vendas"].aplicar_promocao(id_venda, codigo_promocao)
                    
                    # Botão para emitir nota fiscal
                    if st.button("Emitir Nota Fiscal"):
                        nota_fiscal = sistema["vendas"].emissao_nota_fiscal(id_venda, desconto)
                        st.code(nota_fiscal, language=None)
                        
                        # Opção para salvar em arquivo
                        if st.download_button(
                            label="Baixar Nota Fiscal",
                            data=nota_fiscal,
                            file_name=f"nota_fiscal_{id_venda}.txt",
                            mime="text/plain"
                        ):
                            show_success("Nota fiscal baixada com sucesso!")
                else:
                    st.warning(f"Venda com ID '{id_venda}' não encontrada.")
            except Exception as e:
                show_error(f"Erro ao obter venda: {str(e)}")

# =========== RELATÓRIOS ===========
elif selected_menu == "Relatórios":
    st.markdown("<h2 class='section-header'>Relatórios</h2>", unsafe_allow_html=True)
        
    # Submenu para Relatórios
    relatorio_submenu = st.radio(
        "Selecione o Relatório",
        ["Vendas por Período", "Estoque Atual", "Produtos Mais Vendidos", "Clientes Top", "Movimentações de Estoque"]
    )
    
    if relatorio_submenu == "Vendas por Período":
        st.subheader("Relatório de Vendas por Período")
        
        show_instructions("""
        Selecione o período para gerar o relatório de vendas.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input(
                "Data Inicial", 
                value=dt.datetime.now() - dt.timedelta(days=30)
            )
        
        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=dt.datetime.now()
            )
        
        # Converter para datetime com hora
        data_inicio = dt.datetime.combine(data_inicio, dt.time.min)
        data_fim = dt.datetime.combine(data_fim, dt.time.max)
        
        if st.button("Gerar Relatório"):
            # Usar a função de relatório do backend
            # Como a função só imprime, vamos capturar o resultado em um DataFrame para exibir
            vendas = db["vendas"].find({
                "data_venda": {
                    "$gte": data_inicio,
                    "$lte": data_fim
                }
            })

            vendas_lista = list(vendas)
            
            if vendas_lista:
                # Converter para DataFrame
                df_vendas = pd.DataFrame([
                    {
                        "Data": v.get("data_venda", "").strftime("%d/%m/%Y %H:%M"),
                        "Produto": db["estoque_produtos"].find_one({"cod_produto": v.get("cod_produto", "")}).get("nome", ""),
                        "Cliente": db["clientes"].find_one({"cpf": v.get("cpf_cliente", "")}).get("nome", ""),
                        "Quantidade": v.get("qnt_vendida", 0),
                        "Valor Total": v.get("valor_total", 0)
                    }
                    for v in vendas_lista
                ])
                
                # Exibir tabela
                df_vendas_display = df_vendas.copy()
                df_vendas_display["Valor Total"] = df_vendas_display["Valor Total"].apply(lambda x: f"R$ {x:.2f}")
                st.dataframe(df_vendas_display, use_container_width=True)
                
                # Resumo
                total_vendas = len(vendas_lista)
                valor_total = sum(v.get("valor_total", 0) for v in vendas_lista)
                ticket_medio = valor_total / total_vendas if total_vendas > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Vendas", f"{total_vendas}")
                
                with col2:
                    st.metric("Valor Total", f"R$ {valor_total:.2f}")
                
                with col3:
                    st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
                
                # Gráficos
                st.subheader("Valor de Vendas por Dia")
                
                # Agrupar vendas por dia
                df_vendas["Data_Dia"] = pd.to_datetime(df_vendas["Data"]).dt.date
                vendas_por_dia = df_vendas.groupby("Data_Dia")["Valor Total"].sum().reset_index()
                
                fig = px.line(vendas_por_dia, x="Data_Dia", y="Valor Total", markers=True)
                fig.update_layout(yaxis_title="Valor Total (R$)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Vendas por produto
                st.subheader("Vendas por Produto")
                
                vendas_por_produto = df_vendas.groupby("Produto").agg({
                    "Quantidade": "sum",
                    "Valor Total": "sum"
                }).reset_index()
                
                fig = px.bar(vendas_por_produto, x="Produto", y="Valor Total", color="Produto")
                st.plotly_chart(fig, use_container_width=True)
                
                # Opção para exportar
                csv = df_vendas.to_csv(index=False)
                
                st.download_button(
                    label="Exportar Relatório (CSV)",
                    data=csv,
                    file_name=f"relatorio_vendas_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Não há vendas no período selecionado.")
    
    elif relatorio_submenu == "Estoque Atual":
        st.subheader("Relatório de Estoque Atual")
        
        show_instructions("""
        Visualize a situação atual do estoque, ordenado por quantidade ou valor.
        """)
        
        ordenar_por = st.radio(
            "Ordenar por",
            ["Quantidade", "Valor em Estoque"]
        )
        
        if st.button("Gerar Relatório"):
            # Buscar produtos do banco
            produtos = sistema["produtos"].obter_todos_produtos()
            
            if produtos:
                # Ordenar conforme seleção
                if ordenar_por == "Quantidade":
                    produtos_ordenados = sorted(produtos, key=lambda x: x.get("qnt_estoque", 0), reverse=True)
                else:  # Valor em Estoque
                    produtos_ordenados = sorted(
                        produtos, 
                        key=lambda x: x.get("qnt_estoque", 0) * x.get("preco", 0), 
                        reverse=True
                    )
                
                # Converter para DataFrame
                df_estoque = pd.DataFrame([
                    {
                        "Produto": p.get("nome", ""),
                        "Código": p.get("cod_produto", ""),
                        "Categoria": p.get("categoria", ""),
                        "Quantidade": p.get("qnt_estoque", 0),
                        "Preço Unitário": p.get("preco", 0),
                        "Valor em Estoque": p.get("qnt_estoque", 0) * p.get("preco", 0)
                    }
                    for p in produtos_ordenados
                ])
                
                # Formatar valores monetários
                df_estoque_display = df_estoque.copy()
                df_estoque_display["Preço Unitário"] = df_estoque_display["Preço Unitário"].apply(lambda x: f"R$ {x:.2f}")
                df_estoque_display["Valor em Estoque"] = df_estoque_display["Valor em Estoque"].apply(lambda x: f"R$ {x:.2f}")
                
                # Exibir tabela
                st.dataframe(df_estoque_display, use_container_width=True)
                
                # Resumo
                total_produtos = len(produtos)
                total_itens = sum(p.get("qnt_estoque", 0) for p in produtos)
                valor_total_estoque = sum(p.get("qnt_estoque", 0) * p.get("preco", 0) for p in produtos)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Produtos", f"{total_produtos}")
                
                with col2:
                    st.metric("Total de Itens", f"{total_itens}")
                
                with col3:
                    st.metric("Valor Total em Estoque", f"R$ {valor_total_estoque:.2f}")
                
                # Gráficos
                st.subheader("Quantidade por Produto")
                
                # Remover formatação para gráficos
                df_grafico = pd.DataFrame([
                    {
                        "Produto": p.get("nome", ""),
                        "Quantidade": p.get("qnt_estoque", 0),
                        "Valor em Estoque": p.get("qnt_estoque", 0) * p.get("preco", 0),
                        "Categoria": p.get("categoria", "")
                    }
                    for p in produtos_ordenados
                ])
                
                # Top 10 produtos por quantidade
                df_top10_qtd = df_grafico.sort_values("Quantidade", ascending=False).head(10)
                
                fig = px.bar(df_top10_qtd, x="Produto", y="Quantidade", color="Categoria")
                st.plotly_chart(fig, use_container_width=True)
                
                # Top 10 produtos por valor em estoque
                df_top10_valor = df_grafico.sort_values("Valor em Estoque", ascending=False).head(10)
                
                fig = px.bar(df_top10_valor, x="Produto", y="Valor em Estoque", color="Categoria")
                st.plotly_chart(fig, use_container_width=True)
                
                # Distribuição por categoria
                df_categoria = df_grafico.groupby("Categoria").agg({
                    "Quantidade": "sum",
                    "Valor em Estoque": "sum"
                }).reset_index()
                
                # Gráfico de pizza para distribuição de valor por categoria
                fig = px.pie(
                    df_categoria,
                    values="Valor em Estoque",
                    names="Categoria",
                    title="Distribuição do Valor em Estoque por Categoria"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Opção para exportar
                csv = df_estoque.to_csv(index=False)
                
                st.download_button(
                    label="Exportar Relatório (CSV)",
                    data=csv,
                    file_name="relatorio_estoque.csv",
                    mime="text/csv"
                )
            else:
                st.info("Não há produtos cadastrados no sistema.")
    
    elif relatorio_submenu == "Produtos Mais Vendidos":
        st.subheader("Relatório de Produtos Mais Vendidos")
        
        show_instructions("""
        Visualize os produtos mais vendidos por número de compras ou valor gasto.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            limite = st.number_input("Quantidade de Produtos", min_value=1, max_value=50, value=10)
        
        with col2:
            ordenar_por = st.radio(
                "Ordenar por",
                ["Quantidade Vendida", "Valor Total"]
            )
        
        data_inicio = st.date_input(
            "A partir de", 
            value=dt.datetime.now() - dt.timedelta(days=365)
        )
        
        data_inicio = dt.datetime.combine(data_inicio, dt.time.min)
        
        if st.button("Gerar Relatório"):
            # Usar agregação do MongoDB para obter produtos mais vendidos
            pipeline = []
            
            # Filtro de data
            pipeline.append({
                "$match": {
                    "data_venda": {"$gte": data_inicio}
                }
            })
            
            # Agrupamento
            pipeline.append({
                "$group": {
                    "_id": "$cod_produto",
                    "total_vendas": {"$sum": "$qnt_vendida"},
                    "valor_total": {"$sum": "$valor_total"}
                }
            })
            
            # Ordenação
            sort_field = "total_vendas" if ordenar_por == "Quantidade Vendida" else "valor_total"
            pipeline.append({
                "$sort": {sort_field: -1}
            })
            
            # Limite
            pipeline.append({
                "$limit": limite
            })
            
            # Executar pipeline
            produtos_mais_vendidos = list(db["vendas"].aggregate(pipeline))
            
            if produtos_mais_vendidos:
                # Buscar informações adicionais dos produtos
                produtos_info = []
                for p in produtos_mais_vendidos:
                    produto = db["estoque_produtos"].find_one({"cod_produto": p["_id"]})
                    if produto:
                        produtos_info.append({
                            "Produto": produto.get("nome", ""),
                            "Código": p["_id"],
                            "Categoria": produto.get("categoria", ""),
                            "Quantidade Vendida": p["total_vendas"],
                            "Valor Total": p["valor_total"],
                            "Preço Médio": p["valor_total"] / p["total_vendas"]
                        })
                
                # Converter para DataFrame
                df_produtos_vendidos = pd.DataFrame(produtos_info)
                
                # Formatar valores monetários
                df_produtos_vendidos_display = df_produtos_vendidos.copy()
                df_produtos_vendidos_display["Valor Total"] = df_produtos_vendidos_display["Valor Total"].apply(lambda x: f"R$ {x:.2f}")
                df_produtos_vendidos_display["Preço Médio"] = df_produtos_vendidos_display["Preço Médio"].apply(lambda x: f"R$ {x:.2f}")
                
                # Exibir tabela
                st.dataframe(df_produtos_vendidos_display, use_container_width=True)
                
                # Gráficos
                df_grafico = pd.DataFrame(produtos_info)
                
                if ordenar_por == "Quantidade Vendida":
                    st.subheader("Produtos por Quantidade Vendida")
                    
                    # Definir cores para o gráfico baseado na posição
                    cores = px.colors.sequential.Blues_r[:len(df_produtos_vendidos)]
                    
                    fig = px.bar(
                        df_produtos_vendidos.sort_values("Quantidade Vendida", ascending=False),
                        x="Produto",
                        y="Quantidade Vendida",
                        color="Produto",
                        title=f"Top {min(len(df_produtos_vendidos), 10)} Produtos Mais Vendidos por Quantidade",
                        text_auto=True,
                        color_discrete_sequence=cores
                    )
                    fig.update_layout(
                        xaxis_title="",
                        yaxis_title="Quantidade Vendida",
                        showlegend=False,
                        margin=dict(l=20, r=20, t=60, b=80)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.subheader("Produtos por Valor Total de Vendas")
                    
                    # Definir cores para o gráfico baseado na posição
                    cores = px.colors.sequential.Blues_r[:len(df_produtos_vendidos)]
                    
                    fig = px.bar(
                        df_produtos_vendidos.sort_values("Valor Total", ascending=False),
                        x="Produto",
                        y="Valor Total",
                        color="Produto",
                        title=f"Top {min(len(df_produtos_vendidos), 10)} Produtos Mais Vendidos por Valor",
                        text_auto='.2s',
                        color_discrete_sequence=cores
                    )
                    fig.update_layout(
                        xaxis_title="",
                        yaxis_title="Valor Total (R$)",
                        yaxis=dict(tickprefix="R$ "),
                        showlegend=False,
                        margin=dict(l=20, r=20, t=60, b=80)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Adicionar gráfico de pizza para distribuição percentual
                st.subheader("Distribuição Percentual")
                
                if ordenar_por == "Quantidade Vendida":
                    fig2 = px.pie(
                        df_produtos_vendidos,
                        values="Quantidade Vendida",
                        names="Produto",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                else:
                    fig2 = px.pie(
                        df_produtos_vendidos,
                        values="Valor Total",
                        names="Produto",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                
                fig2.update_traces(
                    textposition='inside', 
                    textinfo='percent+label'
                )
                
                fig2.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                    margin=dict(t=30, l=25, r=25, b=25)
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Opção para exportar
                csv = df_produtos_vendidos.to_csv(index=False)
                
                st.download_button(
                    label="Exportar Relatório (CSV)",
                    data=csv,
                    file_name="relatorio_produtos_mais_vendidos.csv",
                    mime="text/csv"
                )
            else:
                st.info("Não há vendas registradas no período selecionado.")
    
    elif relatorio_submenu == "Clientes Top":
        st.subheader("Relatório de Clientes Top")
        
        show_instructions("""
        Visualize os clientes que mais compraram por número de compras ou valor gasto.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            limite = st.number_input("Quantidade de Clientes", min_value=1, max_value=50, value=10)
        
        with col2:
            ordenar_por = st.radio(
                "Ordenar por",
                ["Valor Total", "Quantidade de Compras"]
            )
        
        data_inicio = st.date_input(
            "A partir de", 
            value=dt.datetime.now() - dt.timedelta(days=365)
        )
        
        data_inicio = dt.datetime.combine(data_inicio, dt.time.min)
        
        if st.button("Gerar Relatório"):
            # Usar agregação do MongoDB para obter clientes top
            pipeline = []
            
            # Filtro de data
            pipeline.append({
                "$match": {
                    "data_venda": {"$gte": data_inicio}
                }
            })
            
            # Agrupamento
            pipeline.append({
                "$group": {
                    "_id": "$cpf_cliente",
                    "total_compras": {"$sum": 1},
                    "valor_total": {"$sum": "$valor_total"},
                    "quantidade_produtos": {"$sum": "$qnt_vendida"}
                }
            })
            
            # Ordenação
            sort_field = "valor_total" if ordenar_por == "Valor Total" else "total_compras"
            pipeline.append({
                "$sort": {sort_field: -1}
            })
            
            # Limite
            pipeline.append({
                "$limit": limite
            })
            
            # Executar pipeline
            clientes_top = list(db["vendas"].aggregate(pipeline))
            
            if clientes_top:
                # Buscar informações adicionais dos clientes
                clientes_info = []
                for c in clientes_top:
                    cliente = db["clientes"].find_one({"cpf": c["_id"]})
                    if cliente:
                        clientes_info.append({
                            "Cliente": cliente.get("nome", ""),
                            "CPF": c["_id"],
                            "Total de Compras": c["total_compras"],
                            "Quantidade de Produtos": c["quantidade_produtos"],
                            "Valor Total": c["valor_total"],
                            "Ticket Médio": c["valor_total"] / c["total_compras"]
                        })
                
                # Converter para DataFrame
                df_clientes_top = pd.DataFrame(clientes_info)
                
                # Formatar valores monetários
                df_clientes_top_display = df_clientes_top.copy()
                df_clientes_top_display["Valor Total"] = df_clientes_top_display["Valor Total"].apply(lambda x: f"R$ {x:.2f}")
                df_clientes_top_display["Ticket Médio"] = df_clientes_top_display["Ticket Médio"].apply(lambda x: f"R$ {x:.2f}")
                
                # Exibir tabela
                st.dataframe(df_clientes_top_display, use_container_width=True)
                
                # Gráficos
                df_grafico = pd.DataFrame(clientes_info)
                
                if ordenar_por == "Valor Total":
                    st.subheader("Clientes por Valor Total Gasto")
                    
                    # Definir cores para o gráfico baseado na posição
                    cores = px.colors.sequential.Viridis_r[:len(df_clientes_top)]
                    
                    fig = px.bar(
                        df_clientes_top.sort_values("Valor Total", ascending=False),
                        x="Cliente",
                        y="Valor Total",
                        color="Cliente",
                        title=f"Top {min(len(df_clientes_top), 10)} Clientes por Valor Total Gasto",
                        text_auto='.2s',
                        color_discrete_sequence=cores
                    )
                    fig.update_layout(
                        xaxis_title="",
                        yaxis_title="Valor Total (R$)",
                        yaxis=dict(tickprefix="R$ "),
                        showlegend=False,
                        margin=dict(l=20, r=20, t=60, b=80)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.subheader("Clientes por Número de Compras")
                    
                    # Definir cores para o gráfico baseado na posição
                    cores = px.colors.sequential.Viridis_r[:len(df_clientes_top)]
                    
                    fig = px.bar(
                        df_clientes_top.sort_values("Total de Compras", ascending=False),
                        x="Cliente",
                        y="Total de Compras",
                        color="Cliente",
                        title=f"Top {min(len(df_clientes_top), 10)} Clientes por Número de Compras",
                        text_auto=True,
                        color_discrete_sequence=cores
                    )
                    fig.update_layout(
                        xaxis_title="",
                        yaxis_title="Total de Compras",
                        showlegend=False,
                        margin=dict(l=20, r=20, t=60, b=80)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Adicionar gráfico de treemap para visualização hierárquica
                st.subheader("Treemap de Clientes")
                
                if ordenar_por == "Valor Total":
                    fig2 = px.treemap(
                        df_clientes_top,
                        path=["Cliente"],
                        values="Valor Total",
                        color="Valor Total",
                        color_continuous_scale="Viridis_r",
                        title="Distribuição de Valor por Cliente"
                    )
                else:
                    fig2 = px.treemap(
                        df_clientes_top,
                        path=["Cliente"],
                        values="Total de Compras",
                        color="Total de Compras",
                        color_continuous_scale="Viridis_r",
                        title="Distribuição de Compras por Cliente"
                    )
                
                fig2.update_layout(margin=dict(t=50, l=25, r=25, b=25))
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Opção para exportar
                csv = df_clientes_top.to_csv(index=False)
                
                st.download_button(
                    label="Exportar Relatório (CSV)",
                    data=csv,
                    file_name="relatorio_clientes_top.csv",
                    mime="text/csv"
                )
            else:
                st.info("Não há vendas registradas no período selecionado.")
    
    elif relatorio_submenu == "Movimentações de Estoque":
        st.subheader("Relatório de Movimentações de Estoque")
        
        show_instructions("""
        Visualize as movimentações de estoque (entradas, saídas e ajustes) com filtros por data, produto e tipo.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input(
                "Data Inicial", 
                value=dt.datetime.now() - dt.timedelta(days=30)
            )
        
        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=dt.datetime.now()
            )
        
        # Converter para datetime com hora
        data_inicio = dt.datetime.combine(data_inicio, dt.time.min)
        data_fim = dt.datetime.combine(data_fim, dt.time.max)
        
        # Filtros adicionais
        filtro_tipo = st.radio(
            "Tipo de Movimentação",
            ["Todos", "Entrada", "Saída", "Ajuste"]
        )
        
        tipo_movimentacao = None if filtro_tipo == "Todos" else filtro_tipo.lower()
        
        # Filtro por produto
        produtos = sistema["produtos"].obter_todos_produtos()
        opcoes_produtos = {"": "Todos os Produtos"}
        opcoes_produtos.update({p.get("cod_produto"): f"{p.get('nome')} (Código: {p.get('cod_produto')})" for p in produtos})
        
        cod_produto = st.selectbox(
            "Produto",
            options=list(opcoes_produtos.keys()),
            format_func=lambda x: opcoes_produtos.get(x, x)
        )
        
        if cod_produto == "":
            cod_produto = None
        
        if st.button("Gerar Relatório"):
            try:
                # Chamar a função do relatório, mas vamos capturar o resultado em um DataFrame para exibir
                # Construir filtro para consulta ao MongoDB
                filtro = {}
                
                if data_inicio and data_fim:
                    filtro["data_movimentacao"] = {
                        "$gte": data_inicio,
                        "$lte": data_fim
                    }
                
                if cod_produto:
                    filtro["cod_produto"] = cod_produto
                    
                if tipo_movimentacao:
                    filtro["tipo_movimentacao"] = tipo_movimentacao
                
                # Buscar movimentações
                movimentacoes = db["movimentacoes_estoque"].find(filtro).sort("data_movimentacao", -1)
                
                lista_movimentacoes = list(movimentacoes)
                
                if lista_movimentacoes:
                    # Converter para DataFrame
                    df_movimentacoes = pd.DataFrame([
                        {
                            "Data": mov.get("data_movimentacao", "").strftime("%d/%m/%Y %H:%M"),
                            "Produto": mov.get("nome_produto", ""),
                            "Código": mov.get("cod_produto", ""),
                            "Tipo": mov.get("tipo_movimentacao", "").capitalize(),
                            "Quantidade": mov.get("quantidade", 0),
                            "Estoque Final": mov.get("estoque_resultante", 0),
                            "Motivo": mov.get("motivo", "")
                        }
                        for mov in lista_movimentacoes
                    ])
                    
                    # Formatar quantidade com sinal
                    def formatar_quantidade(row):
                        tipo = row["Tipo"].lower()
                        quantidade = row["Quantidade"]
                        
                        if tipo == "entrada":
                            return f"+{quantidade}"
                        elif tipo == "saida":
                            return f"-{abs(quantidade)}"
                        else:
                            return f"{quantidade:+}" if quantidade != 0 else "0"
                    
                    df_movimentacoes["Quantidade Formatada"] = df_movimentacoes.apply(formatar_quantidade, axis=1)
                    
                    # Exibir tabela
                    st.dataframe(df_movimentacoes[["Data", "Produto", "Tipo", "Quantidade Formatada", "Estoque Final", "Motivo"]], use_container_width=True)
                    
                    # Resumo
                    total_movimentacoes = len(lista_movimentacoes)
                    total_entradas = sum(mov.get("quantidade", 0) for mov in lista_movimentacoes if mov.get("tipo_movimentacao") == "entrada")
                    total_saidas = sum(abs(mov.get("quantidade", 0)) for mov in lista_movimentacoes if mov.get("tipo_movimentacao") == "saida")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total de Movimentações", f"{total_movimentacoes}")
                    
                    with col2:
                        st.metric("Total de Entradas", f"{int(total_entradas)}")
                    
                    with col3:
                        st.metric("Total de Saídas", f"{int(total_saidas)}")
                    
                    # Gráficos
                    st.subheader("Movimentações por Tipo")
                    
                    # Contagem por tipo
                    contagem_por_tipo = df_movimentacoes["Tipo"].value_counts().reset_index()
                    contagem_por_tipo.columns = ["Tipo", "Quantidade"]
                    
                    fig = px.pie(
                        contagem_por_tipo,
                        values="Quantidade",
                        names="Tipo",
                        title="Distribuição de Movimentações por Tipo"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Movimentações por data
                    st.subheader("Movimentações por Data")
                    
                    df_movimentacoes["Data_Dia"] = pd.to_datetime(df_movimentacoes["Data"]).dt.date
                    
                    # Separar por tipo
                    df_pivot = df_movimentacoes.pivot_table(
                        index="Data_Dia",
                        columns="Tipo",
                        values="Quantidade",
                        aggfunc="count",
                        fill_value=0
                    ).reset_index()
                    
                    # Criar gráfico de linha
                    fig = go.Figure()
                    
                    for tipo in df_pivot.columns:
                        if tipo != "Data_Dia":
                            fig.add_trace(go.Scatter(
                                x=df_pivot["Data_Dia"],
                                y=df_pivot[tipo],
                                mode='lines+markers',
                                name=tipo
                            ))
                    
                    fig.update_layout(
                        title="Movimentações por Data e Tipo",
                        xaxis_title="Data",
                        yaxis_title="Quantidade de Movimentações"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Opção para exportar
                    csv = df_movimentacoes.to_csv(index=False)
                    
                    st.download_button(
                        label="Exportar Relatório (CSV)",
                        data=csv,
                        file_name=f"relatorio_movimentacoes_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Nenhuma movimentação encontrada com os filtros especificados.")
            except Exception as e:
                show_error(f"Erro ao gerar relatório de movimentações: {str(e)}")

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #777;">
        Sistema de Gerenciamento de Estoque &copy; 2025 | Desenvolvido usando Python, MongoDB e Streamlit.\n
        Integrantes:
            559666 -  Fabio Renato de Lima Figueiredo
            559977 - Guilherme Henrique Costa de Almeida
            559702 - Renato de Oliveira Barros
            560247 - Vitor Adauto Alves Barobsa
    </div>
    """,
    unsafe_allow_html=True
)


# Fechar conexão com o banco de dados
