from pymongo import MongoClient

try:
    client = MongoClient(
        "mongodb+srv://vitorbarbosa232006:nbz1eG3849AkIj9B@cluster0.o5up1.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true",
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    print(client.list_database_names())
except Exception as e:
    print("Erro de conexão:", e)
