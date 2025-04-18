# ERP Varejo - Checkpoint Python

## Descrição

Este projeto consiste em uma plataforma ERP simplificada para gestão de um varejo de pequeno porte, desenvolvida como parte do Checkpoint da disciplina **Computational Thinking Using Python** (FIAP). A aplicação foi construída utilizando **Python**, **Streamlit** e **MongoDB**, com foco em controle de clientes, estoque, vendas e geração de relatórios.

O objetivo principal do projeto é aplicar conceitos de lógica de programação, persistência de dados, organização modular de código e interface interativa com o usuário.

---

## Funcionalidades

### 1. Gestão de Clientes
- Cadastro de clientes com validação de CPF, e-mail e telefone.
- Listagem e busca de clientes cadastrados.
- Consulta do histórico de compras por cliente.

### 2. Gestão de Estoque
- Adição, remoção e ajuste manual de estoque.
- Alerta de produtos com estoque baixo.

### 3. Gestão de Vendas
- Registro de vendas.
- Aplicação de descontos ou promoções.
- Detalhamento do valor total, descontos e valor final.
- Consulta de vendas por cliente.

### 4. Relatórios
- Geração de relatório de vendas por período.
- Visualização detalhada das vendas dentro do intervalo selecionado.

---

## Estrutura do Projeto

```
📂 cp4_python_erp
├── app_varejo.py             # Código principal do sistema
├── requirements.txt          # Dependências do projeto
├── README.md                 # Informações do projeto
└── .venv/                    # Ambiente virtual
```

---

## Tecnologias Utilizadas

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- PyMongo
- Regex

---

## Como Executar

1. Clone o repositório:
```bash
git clone git@github.com:FabioLimaBR/cp4_python_erp.git
cd cp4_python_erp
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute a aplicação:
```bash
streamlit run app_varejo.py
```

---

## Requisitos

- Python 3.10 ou superior
- MongoDB local ou remoto configurado
- Ambiente virtual configurado

---

## Autores

Projeto acadêmico desenvolvido para a disciplina de Computational Thinking Using Python - FIAP

- **559666 -  Fabio Renato de Lima Figueiredo**
- **559977 - Guilherme Henrique Costa de Almeida**
- **559702 - Renato de Oliveira Barros**
- **560247 - Vitor Adauto Alves Barobsa**

## Licença

Este projeto tem finalidade exclusivamente acadêmica e educativa.
