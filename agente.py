import os
import json

import psycopg
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODELO_EMBEDDINGS = "sentence-transformers/all-MiniLM-L6-v2"
MODELO_LLM = "openai/gpt-oss-120b"

modelo_embeddings = SentenceTransformer(MODELO_EMBEDDINGS)
cliente = Groq(api_key=GROQ_API_KEY)


def buscar_en_base_conocimiento(consulta: str):
    """
    Busca información relevante en PostgreSQL utilizando similitud vectorial.
    """

    embedding = modelo_embeddings.encode(consulta).tolist()

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

            resultados = cursor.fetchall()

    if not resultados:
        return {
            "encontrado": False,
            "resultados": []
        }

    mejor_distancia = float(resultados[0][4])

    # Umbral para evitar responder preguntas totalmente ajenas
    if mejor_distancia > 0.65:
        return {
            "encontrado": False,
            "resultados": []
        }

    documentos = []

    for resultado in resultados:
        faq_id, categoria, pregunta, respuesta, distancia = resultado

        documentos.append({
            "faq_id": faq_id,
            "categoria": categoria,
            "pregunta": pregunta,
            "respuesta": respuesta,
            "distancia": float(distancia),
        })

    return {
        "encontrado": True,
        "resultados": documentos
    }


tools = [
    {
        "type": "function",
        "function": {
            "name": "buscar_en_base_conocimiento",
            "description": (
                "Busca información en la base de conocimientos oficial "
                "de Parachute S.A. Debe utilizarse para responder preguntas "
                "sobre el evento, requisitos, precios, seguridad, ubicación "
                "u otros temas relacionados con Parachute S.A."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": (
                            "Pregunta o consulta que se desea buscar "
                            "en la base de conocimientos."
                        ),
                    }
                },
                "required": ["consulta"],
            },
        },
    }
]


SYSTEM_PROMPT = """
Eres un agente de atención al cliente de Parachute S.A.

Debes responder únicamente utilizando información encontrada
en la base de conocimientos de Parachute S.A.

Para responder preguntas relacionadas con Parachute S.A.,
debes utilizar la herramienta buscar_en_base_conocimiento.

No debes utilizar conocimientos externos.

No inventes datos ni completes información que no aparezca
en los resultados de la herramienta.

Si la herramienta indica que no existe información relevante
para responder la pregunta, debes decir claramente:

"La base de conocimientos no contiene información suficiente 
para responder esa pregunta."

Responde de forma clara, breve y natural.

No utilices formato Markdown. Responde en texto plano.
"""


def ejecutar_agente(pregunta):
    mensajes = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": pregunta
        }
    ]

    respuesta = cliente.chat.completions.create(
        model=MODELO_LLM,
        messages=mensajes,
        tools=tools,
        tool_choice="auto",
    )

    mensaje = respuesta.choices[0].message

    if not mensaje.tool_calls:
        return mensaje.content

    mensajes.append(mensaje)

    for tool_call in mensaje.tool_calls:
        if tool_call.function.name == "buscar_en_base_conocimiento":

            argumentos = json.loads(tool_call.function.arguments)

            resultado = buscar_en_base_conocimiento(
                argumentos["consulta"]
            )

            mensajes.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        resultado,
                        ensure_ascii=False
                    ),
                }
            )

    respuesta_final = cliente.chat.completions.create(
        model=MODELO_LLM,
        messages=mensajes,
        tools=tools,
    )

    return respuesta_final.choices[0].message.content


def main():
    print("=" * 60)
    print("AGENTE DE PREGUNTAS FRECUENTES - PARACHUTE S.A.")
    print("=" * 60)
    print("Ingrese 'Bye' para salir.")
    print("También puede usar Ctrl+C.")
    print()

    while True:
        try:
            pregunta = input("User: ").strip()

            if not pregunta:
                continue

            if pregunta.lower() == "bye":
                print("Agent: ¡Bye!")
                break

            respuesta = ejecutar_agente(pregunta)

            print(f"\nAgent: {respuesta}\n")

        except KeyboardInterrupt:
            print("\n\nAgent: ¡Bye!")
            break


if __name__ == "__main__":
    main()