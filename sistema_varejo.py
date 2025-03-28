from pymongo import MongoClient
import datetime as dt
from bson import ObjectId
# Cadastrar produtos

class GerenciadorProdutos:
    def __init__(self, mongodb_uri="mongodb+srv://vitorbarbosa232006:nbz1eG3849AkIj9B@cluster0.o5up1.mongodb.net/"):

        # Conectar ao MongoDB

        self._client = MongoClient(mongodb_uri)
        self._db = self._client["Varejo_Python"]
        self._colecao_produtos = self._db["estoque_produtos"]
    
    def cadastrar_produto(self, nome, cod_produto, categoria, qnt_estoque, preco, descricao, fornecedor):

        # Validações básicas

        if not nome or not cod_produto:
            raise ValueError("Nome e código do produto são obrigatórios")
            
        if qnt_estoque < 0 or preco < 0:
            raise ValueError("Quantidade e preço não podem ser negativos")
            
        # Verificar se código já existe

        if self._colecao_produtos.find_one({"cod_produto": cod_produto}):
            raise ValueError(f"Produto com código {cod_produto} já cadastrado")
        
        # Criar dicionário com os dados do produto

        produto = {
            "nome": nome,
            "cod_produto": cod_produto,
            "categoria": categoria,
            "qnt_estoque": qnt_estoque,
            "preco": preco,
            "descricao": descricao,
            "fornecedor": fornecedor
        }
        
        # Inserir no MongoDB

        resultado = self._colecao_produtos.insert_one(produto)
        
        # Retornar o produto com o ID gerado pelo MongoDB

        produto["_id"] = resultado.inserted_id
        return produto
    
    def obter_todos_produtos(self):

        """Retorna todos os produtos do banco de dados"""

        return list(self._colecao_produtos.find())
    
    def obter_produto(self, cod_produto):

        """Retorna um produto específico pelo código"""

        return self._colecao_produtos.find_one({"cod_produto": cod_produto})
    

gerenciador = GerenciadorProdutos()

class GestaoEstoque:
    # Adicionar na classe GestaoEstoque:

    def __init__(self, gerenciador_produtos, mongodb_uri="mongodb+srv://vitorbarbosa232006:nbz1eG3849AkIj9B@cluster0.o5up1.mongodb.net/"):
        self._gerenciador_produtos = gerenciador_produtos
        
        # Conectar ao MongoDB
        self._client = MongoClient(mongodb_uri)
        self._db = self._client["Varejo_Python"]
        self._colecao_estoque = self._db["estoque_produtos"]
        self._colecao_movimentacoes = self._db["movimentacoes_estoque"]  # Nova coleção

    def _registrar_movimentacao(self, cod_produto, quantidade, tipo_movimentacao, motivo=""):
        """Registra uma movimentação de estoque"""
        produto = self._gerenciador_produtos.obter_produto(cod_produto)
        if not produto:
            raise ValueError(f"Produto com código {cod_produto} não encontrado")
        
        # Nota: estoque_resultante está obtendo o valor antigo do estoque
        # Melhor atualizar para buscar o produto novamente após a atualização
        
        movimentacao = {
            "cod_produto": cod_produto,
            "nome_produto": produto["nome"],
            "quantidade": quantidade,
            "tipo_movimentacao": tipo_movimentacao,
            "estoque_resultante": produto["qnt_estoque"],  # Aqui está o valor antigo
            "data_movimentacao": dt.datetime.now(),
            "motivo": motivo
        }
        
        self._colecao_movimentacoes.insert_one(movimentacao)
        return movimentacao
    
    # Modificar o método adicionar_estoque:

    def adicionar_estoque(self, cod_produto, qnt_adicional, motivo="Entrada padrão"):
        # Verificar se o produto existe
        produto = self._gerenciador_produtos.obter_produto(cod_produto)
        if not produto:
            raise ValueError(f"Produto com código {cod_produto} não encontrado")
        
        # Atualizar a quantidade em estoque
        qnt_total = produto["qnt_estoque"] + qnt_adicional
        self._colecao_estoque.update_one({"cod_produto": cod_produto}, {"$set": {"qnt_estoque": qnt_total}})
        
        # Registrar movimentação
        self._registrar_movimentacao(cod_produto, qnt_adicional, "entrada", motivo)
        
        return f"Estoque do produto {cod_produto} atualizado para {qnt_total}"

    # Modificar o método remover_estoque:
    def remover_estoque(self, cod_produto, qnt_remover, motivo="Saída padrão"):
        # Verificar se a quantidade a remover é válida
        if qnt_remover <= 0:
            raise ValueError("A quantidade a remover deve ser maior que zero")

        # Verificar se o produto existe
        produto = self._gerenciador_produtos.obter_produto(cod_produto)
        if not produto:
            raise ValueError(f"Produto com código {cod_produto} não encontrado")

        # Verificar se há estoque suficiente
        qnt_estoque_atual = produto.get("qnt_estoque", 0)
        if qnt_remover > qnt_estoque_atual:
            raise ValueError(
                f"Estoque insuficiente. Disponível: {qnt_estoque_atual}, Tentativa de remover: {qnt_remover}"
            )

        # Atualizar o estoque no banco de dados
        novo_estoque = qnt_estoque_atual - qnt_remover
        try:
            self._colecao_estoque.update_one(
                {"cod_produto": cod_produto},
                {"$set": {"qnt_estoque": novo_estoque}}
            )
        except Exception as e:
            raise RuntimeError(f"Falha ao atualizar estoque: {str(e)}")

        # Registrar a movimentação de saída
        self._registrar_movimentacao(
            cod_produto, 
            -qnt_remover, 
            tipo_movimentacao="saida", 
            motivo=motivo
        )

        return f"Estoque do produto {cod_produto} atualizado para {novo_estoque}"

    # Modificar o método atualizacao_estoque:
    def atualizacao_estoque(self, cod_produto, qnt_atualizada, motivo="Ajuste de estoque"):
        # Verificar se o produto existe
        produto = self._gerenciador_produtos.obter_produto(cod_produto)
        if not produto:
            raise ValueError(f"Produto com código {cod_produto} não encontrado")
        
        # Calcular a diferença para o registro
        diferenca = qnt_atualizada - produto["qnt_estoque"]
        tipo = "ajuste"
        
        # Atualizar a quantidade em estoque
        self._colecao_estoque.update_one({"cod_produto": cod_produto}, {"$set": {"qnt_estoque": qnt_atualizada}})
        
        # Registrar movimentação
        self._registrar_movimentacao(cod_produto, diferenca, tipo, motivo)
        
        return f"Estoque do produto {cod_produto} atualizado para {qnt_atualizada}"

estoque = GestaoEstoque(gerenciador)

class Cliente:
    def __init__(self, mongodb_uri="mongodb+srv://vitorbarbosa232006:nbz1eG3849AkIj9B@cluster0.o5up1.mongodb.net/"):

        # Conectar ao MongoDB

        self._client = MongoClient(mongodb_uri)
        self._db = self._client["Varejo_Python"]
        self._colecao_clientes = self._db["clientes"]
    
    def cadastro(self, nome, cpf, email, telefone):

        # Validações básicas

        if not nome or not cpf:
            raise ValueError("Nome e CPF do cliente são obrigatórios")
        
        # Verificar se CPF já existe

        if self._colecao_clientes.find_one({"cpf": cpf}):
            raise ValueError(f"Cliente com CPF {cpf} já cadastrado")
        
        # Criar dicionário com os dados do cliente

        cliente = {
            "nome": nome,
            "cpf": cpf,
            "email": email,
            "telefone": telefone
        }
        
        # Inserir no MongoDB

        resultado = self._colecao_clientes.insert_one(cliente)
        
        # Retornar o cliente com o ID gerado pelo MongoDB

        cliente["_id"] = resultado.inserted_id
        return cliente
    
    def obter_todos_clientes(self):

        """Retorna todos os clientes do banco de dados"""

        return list(self._colecao_clientes.find())
    
    def obter_cliente(self, cpf):

        """Retorna um cliente específico pelo CPF"""

        return self._colecao_clientes.find_one({"cpf": cpf})
    
cliente_manager = Cliente()
    
class Vendas:
    def __init__(self, gerenciador_produtos, gerenciador_clientes, gestor_estoque, mongodb_uri="mongodb+srv://vitorbarbosa232006:nbz1eG3849AkIj9B@cluster0.o5up1.mongodb.net/"):
        self._gerenciador_produtos = gerenciador_produtos
        self._gerenciador_clientes = gerenciador_clientes
        self._gestor_estoque = gestor_estoque

        # Conectar ao MongoDB

        self._client = MongoClient(mongodb_uri)
        self._db = self._client["Varejo_Python"]
        self._colecao_vendas = self._db["vendas"]
    
    def registrar_venda(self, cod_produto, cpf_cliente, qnt_vendida):

        # Verificar se o produto existe

        produto = self._gerenciador_produtos.obter_produto(cod_produto)
        if not produto:
            raise ValueError(f"Produto com código {cod_produto} não encontrado")
        
        # Verificar se o cliente existe

        cliente_info = self._gerenciador_clientes.obter_cliente(cpf_cliente)
        if not cliente_info:
            raise ValueError(f"Cliente com CPF {cpf_cliente} não encontrado")
        
        # Verificar se há estoque suficiente

        qnt_total = produto["qnt_estoque"]
        if qnt_vendida > qnt_total:
            raise ValueError(f"Estoque insuficiente para vender {qnt_vendida} unidades")
        
        # Atualizar a quantidade em estoque

        qnt_total -= qnt_vendida
        self._gestor_estoque.atualizacao_estoque(cod_produto, qnt_total)

        
        # Calcular o valor total da venda

        valor_total = produto["preco"] * qnt_vendida
        
        # Criar dicionário com os dados da venda

        venda = {
            "cod_produto": cod_produto,
            "cpf_cliente": cpf_cliente,
            "qnt_vendida": qnt_vendida,
            "valor_total": valor_total,
            "data_venda": dt.datetime.now()
        }
        
        # Inserir no MongoDB

        resultado = self._colecao_vendas.insert_one(venda)
        
        # Retornar a venda com o ID gerado pelo MongoDB

        venda["_id"] = resultado.inserted_id
        return venda
    
    def obter_todas_vendas(self):

        # Retorna todas as vendas do banco de dados 

        return list(self._colecao_vendas.find())
    
    def obter_venda(self, id_venda):

        # Retorna uma venda específica pelo ID 

        id_venda = ObjectId(id_venda)

        return self._colecao_vendas.find_one({"_id": id_venda})
    
    def obter_venda_por_cliente(self, cpf_cliente):

        # Retorna todas as vendas de um cliente específico pelo CPF 

        return list(self._colecao_vendas.find({"cpf_cliente": cpf_cliente}))
    
    def emissao_nota_fiscal(self, id_venda, desconto=None):
        """

        Emite nota fiscal com desconto opcional

        """

        id_venda = ObjectId(id_venda)

        venda = self.obter_venda(id_venda)
        if not venda:
            raise ValueError(f"Venda com ID {id_venda} não encontrada")
        
        produto = self._gerenciador_produtos.obter_produto(venda["cod_produto"])
        cliente = self._gerenciador_clientes.obter_cliente(venda["cpf_cliente"])
        
        valor_total = venda["valor_total"]
        valor_final = valor_total
        info_desconto = ""
        
        if desconto:
            valor_final = desconto["valor_final"]
            info_desconto = f"""
            Desconto aplicado: R$ {desconto['desconto_aplicado']:.2f}
            Tipo de desconto: {desconto['tipo_desconto']}"""
            if "promocao" in desconto:
                info_desconto += f"\nPromoção: {desconto['promocao']['descricao']}"
        
        nota_fiscal = f"""
        ============ NOTA FISCAL ============
        Empresa: Varejo Python
        Data: {venda["data_venda"].strftime("%d/%m/%Y %H:%M:%S")}
        Cliente: {cliente["nome"]} (CPF: {cliente["cpf"]})
        Produto: {produto["nome"]} (Código: {produto["cod_produto"]})
        Quantidade: {venda["qnt_vendida"]} unidades
        Valor original: R$ {valor_total:.2f}{info_desconto}
        Valor final: R$ {valor_final:.2f}
        """
        
        return nota_fiscal
    
    def descontos(self, id_venda, valor_desconto, tipo_desconto="valor"):
        """
        Calcula o desconto na venda sem alterar o valor original no banco
        tipo_desconto: "valor" para desconto em R$, "porcentagem" para desconto em %
        """
        # Obter a venda pelo ID

        id_venda = ObjectId(id_venda)

        venda = self.obter_venda(id_venda)
        if not venda:
            raise ValueError(f"Venda com ID {id_venda} não encontrada")
        
        valor_original = venda["valor_total"]
        
        # Definir limites de desconto
        LIMITE_MAXIMO_PORCENTAGEM = 30  # 30% de desconto máximo
        LIMITE_MAXIMO_VALOR = valor_original * 0.3  # Máximo 50% do valor em R$
        
        if tipo_desconto == "porcentagem":
            if valor_desconto > LIMITE_MAXIMO_PORCENTAGEM:
                raise ValueError(f"Desconto máximo permitido é {LIMITE_MAXIMO_PORCENTAGEM}%")
            valor_desconto_real = valor_original * (valor_desconto / 100)
        else:  # tipo_desconto == "valor"
            if valor_desconto > LIMITE_MAXIMO_VALOR:
                raise ValueError(f"Desconto máximo permitido é R$ {LIMITE_MAXIMO_VALOR:.2f}")
            valor_desconto_real = valor_desconto
        
        # Calcular valor final com desconto
        valor_final = valor_original - valor_desconto_real
        
        return {
            "valor_original": valor_original,
            "desconto_aplicado": valor_desconto_real,
            "valor_final": valor_final,
            "tipo_desconto": tipo_desconto,
            "id_venda": id_venda
        }

    def aplicar_promocao(self, id_venda, codigo_promocao):
        """
        Aplica promoções especiais baseadas em códigos promocionais
        """

        id_venda = ObjectId(id_venda)

        promocoes = {
            "PRIMEIRA_COMPRA": {"desconto": 15, "tipo": "porcentagem", "descricao": "15% na primeira compra"},
            "CLIENTE_VIP": {"desconto": 50, "tipo": "valor", "descricao": "R$ 50,00 de desconto VIP"},
            "BLACK_FRIDAY": {"desconto": 25, "tipo": "porcentagem", "descricao": "25% na Black Friday"},
            "FRETE_GRATIS": {"desconto": 20, "tipo": "valor", "descricao": "R$ 20,00 de desconto no frete"}
        }
        
        if codigo_promocao not in promocoes:
            raise ValueError("Código de promoção inválido")
        
        promocao = promocoes[codigo_promocao]
        resultado = self.descontos(
            id_venda, 
            promocao["desconto"], 
            tipo_desconto=promocao["tipo"]
        )
        
        # Adicionar informações da promoção ao resultado
        resultado["promocao"] = {
            "codigo": codigo_promocao,
            "descricao": promocao["descricao"]
        }
        
        return resultado
    
vender = Vendas(gerenciador, cliente_manager, estoque)
    
class Relatorios:
    def __init__(self, mongodb_uri="mongodb+srv://vitorbarbosa232006:nbz1eG3849AkIj9B@cluster0.o5up1.mongodb.net/"):
        # Conectar ao MongoDB
        self._client = MongoClient(mongodb_uri)
        self._db = self._client["Varejo_Python"]
        self._colecao_vendas = self._db["vendas"]
        self._colecao_produtos = self._db["estoque_produtos"]
        self._colecao_clientes = self._db["clientes"]

    def relatorio_vendas_periodo(self, data_inicio, data_fim):
        """Gera relatório de vendas em um período específico"""
        vendas = self._colecao_vendas.find({
            "data_venda": {
                "$gte": data_inicio,
                "$lte": data_fim
            }
        })

        total_vendas = 0
        qtd_vendas = 0
        
        print("\n=== RELATÓRIO DE VENDAS ===")
        print(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
        print("-" * 50)

        for venda in vendas:
            produto = self._colecao_produtos.find_one({"cod_produto": venda["cod_produto"]})
            cliente = self._colecao_clientes.find_one({"cpf": venda["cpf_cliente"]})
            
            print(f"Data: {venda['data_venda'].strftime('%d/%m/%Y %H:%M')}")
            print(f"Produto: {produto['nome']}")
            print(f"Cliente: {cliente['nome']}")
            print(f"Valor: R$ {venda['valor_total']:.2f}")
            print("-" * 50)
            
            total_vendas += venda["valor_total"]
            qtd_vendas += 1

        print(f"\nTotal de vendas: {qtd_vendas}")
        print(f"Valor total: R$ {total_vendas:.2f}")
        print(f"Ticket médio: R$ {(total_vendas/qtd_vendas if qtd_vendas > 0 else 0):.2f}")

    def relatorio_estoque(self, ordenar_por="qnt_estoque"):
        """Gera relatório do estoque atual, ordenado por quantidade ou valor"""
        produtos = self._colecao_produtos.find().sort(ordenar_por)

        print("\n=== RELATÓRIO DE ESTOQUE ===")
        print("-" * 50)

        valor_total_estoque = 0
        for produto in produtos:
            valor_estoque = produto["qnt_estoque"] * produto["preco"]
            valor_total_estoque += valor_estoque
            
            print(f"Produto: {produto['nome']}")
            print(f"Código: {produto['cod_produto']}")
            print(f"Quantidade: {produto['qnt_estoque']}")
            print(f"Valor unitário: R$ {produto['preco']:.2f}")
            print(f"Valor em estoque: R$ {valor_estoque:.2f}")
            print("-" * 50)

        print(f"\nValor total em estoque: R$ {valor_total_estoque:.2f}")

    def relatorio_produtos_mais_vendidos(self, limite=5):
        """Gera relatório dos produtos mais vendidos"""
        pipeline = [
            {"$group": {
                "_id": "$cod_produto",
                "total_vendas": {"$sum": "$qnt_vendida"},
                "valor_total": {"$sum": "$valor_total"}
            }},
            {"$sort": {"total_vendas": -1}},
            {"$limit": limite}
        ]

        produtos_mais_vendidos = self._colecao_vendas.aggregate(pipeline)

        print("\n=== PRODUTOS MAIS VENDIDOS ===")
        print("-" * 50)

        for rank in produtos_mais_vendidos:
            produto = self._colecao_produtos.find_one({"cod_produto": rank["_id"]})
            print(f"Produto: {produto['nome']}")
            print(f"Quantidade vendida: {rank['total_vendas']}")
            print(f"Valor total em vendas: R$ {rank['valor_total']:.2f}")
            print("-" * 50)

    def relatorio_clientes_top(self, limite=5):
        """Gera relatório dos clientes que mais compraram"""
        pipeline = [
            {"$group": {
                "_id": "$cpf_cliente",
                "total_compras": {"$sum": 1},
                "valor_total": {"$sum": "$valor_total"}
            }},
            {"$sort": {"valor_total": -1}},
            {"$limit": limite}
        ]

        clientes_top = self._colecao_vendas.aggregate(pipeline)

        print("\n=== CLIENTES TOP ===")
        print("-" * 50)

        for rank in clientes_top:
            cliente = self._colecao_clientes.find_one({"cpf": rank["_id"]})
            print(f"Cliente: {cliente['nome']}")
            print(f"Total de compras: {rank['total_compras']}")
            print(f"Valor total gasto: R$ {rank['valor_total']:.2f}")
            print("-" * 50)
    

    def relatorio_movimentacoes(self, data_inicio=None, data_fim=None, cod_produto=None, tipo_movimentacao=None):
        """
        Gera relatório de movimentações de estoque com filtros opcionais
        """
        # Construir o filtro com base nos parâmetros
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
        movimentacoes = self._colecao_movimentacoes.find(filtro).sort("data_movimentacao", -1)  # Mais recentes primeiro
        
        # Converter para lista para verificar se há movimentações
        lista_movimentacoes = list(movimentacoes)
        
        if not lista_movimentacoes:
            print("Nenhuma movimentação encontrada com os filtros especificados.")
            return []
        
        # Exibir o relatório
        print("\n=== RELATÓRIO DE MOVIMENTAÇÕES DE ESTOQUE ===")
        
        # Exibir filtros aplicados
        if data_inicio and data_fim:
            print(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
        
        if cod_produto:
            produto = self._colecao_produtos.find_one({"cod_produto": cod_produto})
            if produto:
                print(f"Produto: {produto['nome']} (Código: {cod_produto})")
        
        if tipo_movimentacao:
            print(f"Tipo de movimentação: {tipo_movimentacao.capitalize()}")
        
        print("-" * 70)
        print(f"{'Data':<16} {'Produto':<25} {'Tipo':<10} {'Quantidade':<12} {'Estoque Final':<15} {'Motivo':<20}")
        print("-" * 70)
        
        for mov in lista_movimentacoes:
            data_str = mov["data_movimentacao"].strftime("%d/%m/%Y %H:%M")
            nome_produto = mov["nome_produto"][:23] + ".." if len(mov["nome_produto"]) > 25 else mov["nome_produto"]
            tipo = mov["tipo_movimentacao"].capitalize()
            quantidade = mov["quantidade"]
            estoque_final = mov["estoque_resultante"]
            motivo = mov.get("motivo", "")[:18] + ".." if len(mov.get("motivo", "")) > 20 else mov.get("motivo", "")
            
            # Formatação de quantidade (+ para entrada, - para saída)
            if mov["tipo_movimentacao"] == "entrada":
                quantidade_formatada = f"+{quantidade}"
            elif mov["tipo_movimentacao"] == "saida":
                quantidade_formatada = f"-{abs(quantidade)}"
            else:
                quantidade_formatada = f"{quantidade:+}" if quantidade != 0 else "0"
            
            print(f"{data_str:<16} {nome_produto:<25} {tipo:<10} {quantidade_formatada:<12} {estoque_final:<15} {motivo}")
        
        print("-" * 70)
        print(f"Total de movimentações: {len(lista_movimentacoes)}")
        
        # Calcular totais por tipo
        entradas = sum(mov["quantidade"] for mov in lista_movimentacoes if mov["tipo_movimentacao"] == "entrada")
        saidas = sum(abs(mov["quantidade"]) for mov in lista_movimentacoes if mov["tipo_movimentacao"] == "saida")
        
        print(f"Total de entradas: {entradas}")
        print(f"Total de saídas: {saidas}")
        
        return lista_movimentacoes
    

# ------------------------------------------------------------------------------------------------------------------------------------------------------------

# Interface Gráfica ( StreamLit )

# app_varejo.py