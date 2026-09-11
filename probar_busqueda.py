import os
import psycopg
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

MODELO_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"

modelo = SentenceTransformer(MODELO_EMBEDDINGS)


def buscar(pregunta):
    embedding = modelo.encode(pregunta).tolist()

    with psycopg.connect(**DB_CONFIG) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    faq_id,
                    categoria,
                    pregunta,
                    respuesta,
                    embedding <=> %s::vector AS distancia
                FROM faqs
                ORDER BY embedding <=> %s::vector
                LIMIT 3;
                """,
                (embedding, embedding),
            )

            return cursor.fetchall()


pregunta = input("Pregunta: ")

resultados = buscar(pregunta)

print("\nResultados más cercanos:\n")

for resultado in resultados:
    faq_id, categoria, pregunta_faq, respuesta, distancia = resultado

    print(f"{faq_id} | {categoria}")
    print(f"Pregunta: {pregunta_faq}")
    print(f"Distancia: {distancia:.4f}")
    print(f"Respuesta: {respuesta}")
    print("-" * 80)