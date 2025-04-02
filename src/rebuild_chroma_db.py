import os
import openai
import chromadb
from dotenv import load_dotenv
from neo4j import GraphDatabase
from uuid import uuid4
from tqdm import tqdm

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_store")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Batch size for OpenAI embedding calls
BATCH_SIZE = 20
COLLECTION_NAME = "linkedin_connections"

def fetch_all_people():
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Person)
            RETURN p.name AS name, p.company AS company, p.position AS position, 
                   coalesce(p.linkedin, 'Unknown') AS url
        """)
        return result.data()

def get_openai_embeddings_batch(texts, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        model=model,
        input=texts
    )
    return [item.embedding for item in response.data]

def repopulate_chroma_store():
    people = fetch_all_people()
    print(f"⚙️ Rebuilding ChromaDB with {len(people)} connections...")

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(name=COLLECTION_NAME)
    except ValueError:
        pass  # Collection didn't exist, safe to ignore

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    documents, metadatas, ids, texts = [], [], [], []

    for person in people:
        # Compose text
        text = f"{person['name']} works at {person['company']} as {person['position']}"
        texts.append(text)
        documents.append(text)
        metadatas.append({
            "name": person["name"] or "Unknown",
            "company": person["company"] or "Unknown",
            "position": person["position"] or "Unknown",
            "url": person["url"] or "Unknown"
        })
        ids.append(str(uuid4()))

    # Process in batches
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="🔁 Embedding"):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_embeddings = get_openai_embeddings_batch(batch_texts)

        collection.add(
            documents=documents[i:i+BATCH_SIZE],
            embeddings=batch_embeddings,
            metadatas=metadatas[i:i+BATCH_SIZE],
            ids=ids[i:i+BATCH_SIZE]
        )

    print("✅ ChromaDB rebuilt successfully.")

if __name__ == "__main__":
    repopulate_chroma_store()