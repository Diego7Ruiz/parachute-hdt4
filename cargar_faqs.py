import re
import json
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

ARCHIVO_FAQS = "Corpus_FAQs_Parachute_SA_2026.txt"
MODELO_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"


def leer_faqs():
    with open(ARCHIVO_FAQS, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    patron = re.compile(
        r"ID:\s*(FAQ-\d+)\s*\n"
        r"CATEGORÍA:\s*(.*?)\s*\n"
        r"PREGUNTA:\s*(.*?)\s*\n"
        r"RESPUESTA:\s*(.*?)\s*\n"
        r"METADATA:\s*(\{.*?\})",
        re.DOTALL,
    )

    faqs = []

    for coincidencia in patron.finditer(contenido):
        faq_id, categoria, pregunta, respuesta, metadata = coincidencia.groups()

        faqs.append({
            "faq_id": faq_id.strip(),
            "categoria": categoria.strip(),
            "pregunta": pregunta.strip(),
            "respuesta": respuesta.strip(),
            "metadata": json.loads(metadata.strip()),
        })

    return faqs


def crear_base():
    with psycopg.connect(**DB_CONFIG) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faqs (
                    id SERIAL PRIMARY KEY,
                    faq_id VARCHAR(20) UNIQUE NOT NULL,
                    categoria TEXT NOT NULL,
                    pregunta TEXT NOT NULL,
                    respuesta TEXT NOT NULL,
                    metadata JSONB,
                    embedding VECTOR(384)
                );
            """)

        conexion.commit()


def cargar_faqs(faqs):
    print("Cargando modelo de embeddings...")
    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    with psycopg.connect(**DB_CONFIG) as conexion:
        with conexion.cursor() as cursor:
            for i, faq in enumerate(faqs, start=1):
                texto_embedding = (
                    f"Categoría: {faq['categoria']}\n"
                    f"Pregunta: {faq['pregunta']}\n"
                    f"Respuesta: {faq['respuesta']}"
                )

                embedding = modelo.encode(texto_embedding).tolist()

                cursor.execute(
                    """
                    INSERT INTO faqs (
                        faq_id,
                        categoria,
                        pregunta,
                        respuesta,
                        metadata,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (faq_id)
                    DO UPDATE SET
                        categoria = EXCLUDED.categoria,
                        pregunta = EXCLUDED.pregunta,
                        respuesta = EXCLUDED.respuesta,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding;
                    """,
                    (
                        faq["faq_id"],
                        faq["categoria"],
                        faq["pregunta"],
                        faq["respuesta"],
                        json.dumps(faq["metadata"]),
                        embedding,
                    ),
                )

                print(f"Cargada {faq['faq_id']} ({i}/{len(faqs)})")

        conexion.commit()


def main():
    print("Leyendo archivo de FAQs...")
    faqs = leer_faqs()

    print(f"Se encontraron {len(faqs)} FAQs.")

    print("Preparando PostgreSQL y pgvector...")
    crear_base()

    print("Generando embeddings...")
    cargar_faqs(faqs)

    print("Carga finalizada correctamente.")


if __name__ == "__main__":
    main()