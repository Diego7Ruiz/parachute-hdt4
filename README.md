# HDT4 - Agente RAG con PostgreSQL y pgvector

Proyecto desarrollado para la Hoja de Trabajo #4 del curso CC3116.

El objetivo es implementar un agente de preguntas frecuentes para Parachute S.A. utilizando una base de datos vectorial en PostgreSQL con la extensión pgvector.

El agente responde preguntas utilizando únicamente la información contenida en el archivo:

`Corpus_FAQs_Parachute_SA_2026.txt`

La solución utiliza embeddings generados localmente con `sentence-transformers` y un modelo de lenguaje consultado mediante Groq.

---

## Tecnologías utilizadas

- Python
- PostgreSQL
- pgvector
- Docker
- sentence-transformers
- Groq API
- psycopg
- python-dotenv

Modelo de embeddings utilizado:

`sentence-transformers/all-MiniLM-L6-v2`

---

## Estructura del proyecto

```text
parachute-HDT4/
│
├── agente.py
├── cargar_faqs.py
├── Corpus_FAQs_Parachute_SA_2026.txt
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Requisitos

Antes de ejecutar el proyecto es necesario tener instalado:

- Python
- Docker Desktop
- Git

Para verificar las instalaciones:

```powershell
python --version
git --version
docker --version
docker compose version
```

---

## 1. Crear entorno virtual

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
```

Activar el entorno virtual en Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución de scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Luego volver a activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 2. Instalar dependencias

Con el entorno virtual activo:

```powershell
pip install -r requirements.txt
```

El archivo `requirements.txt` contiene las librerías necesarias para conectarse a PostgreSQL, generar embeddings y utilizar la API de Groq.

---

## 3. Configurar variables de entorno

Crear un archivo `.env` utilizando `.env.example` como referencia.

Contenido esperado:

```env
GROQ_API_KEY=tu_api_key

DB_HOST=localhost
DB_PORT=5432
DB_NAME=parachute
DB_USER=postgres
DB_PASSWORD=postgres
```

La clave de Groq debe obtenerse desde la consola de Groq.

El archivo `.env` no debe subirse al repositorio.

---

## 4. Inicializar PostgreSQL y pgvector

El proyecto utiliza Docker para ejecutar PostgreSQL con la extensión pgvector.

Ejecutar:

```powershell
docker compose up -d
```

Verificar que el contenedor esté activo:

```powershell
docker ps
```

Debe aparecer un contenedor llamado:

```text
parachute_pgvector
```

---

## 5. Cargar la base de conocimientos

Ejecutar:

```powershell
python cargar_faqs.py
```

Este script realiza las siguientes acciones:

1. Lee el archivo de FAQs.
2. Extrae cada pregunta, respuesta, categoría y metadata.
3. Genera embeddings utilizando `all-MiniLM-L6-v2`.
4. Crea la extensión `pgvector`.
5. Crea la tabla de FAQs.
6. Guarda cada FAQ junto con su embedding en PostgreSQL.

Al finalizar debe mostrarse:

```text
Carga finalizada correctamente.
```

---

## 6. Ejecutar el agente

Después de cargar la base de conocimientos:

```powershell
python agente.py
```

El agente permite realizar múltiples preguntas durante una misma sesión.

Ejemplo:

```text
User: ¿Cuál es el peso máximo para saltar?

Agent: El peso máximo permitido para realizar un salto tándem es 100 kg.
```

También permite realizar consultas relacionadas semánticamente aunque no coincidan exactamente con el texto de las FAQs.

---

## Herramienta de búsqueda

El agente tiene configurada una herramienta llamada:

```text
buscar_en_base_conocimiento
```

Esta herramienta:

1. Convierte la consulta del usuario en un embedding.
2. Busca las FAQs más similares utilizando pgvector.
3. Devuelve la información encontrada al modelo de lenguaje.
4. El modelo genera una respuesta utilizando únicamente esa información.

---

## Preguntas fuera de la base de conocimientos

Si la información solicitada no se encuentra en la base de conocimientos, el agente no debe inventar una respuesta.

Ejemplo:

```text
User: ¿Cuál es la capital de Japón?

Agent: La base de conocimientos no contiene información suficiente para responder esa pregunta.
```

---

## Finalizar el programa

Para salir del agente puede escribir:

```text
Bye
```

También puede utilizar:

```text
Ctrl + C
```

---

## Detener PostgreSQL

Para detener los contenedores:

```powershell
docker compose down
```

Para volver a iniciar el sistema:

```powershell
docker compose up -d
```

---

## Flujo general

```text
Archivo de FAQs
      |
      v
cargar_faqs.py
      |
      v
sentence-transformers
      |
      v
PostgreSQL + pgvector
      |
      v
agente.py
      |
      v
Tool / Function Call
      |
      v
Busqueda vectorial
      |
      v
Respuesta del agente
```

---

## Nota

La base de conocimientos utilizada contiene 120 FAQs de Parachute S.A.

Cada FAQ es almacenada como un registro independiente en PostgreSQL junto con un vector de 384 dimensiones generado por el modelo `all-MiniLM-L6-v2`.
