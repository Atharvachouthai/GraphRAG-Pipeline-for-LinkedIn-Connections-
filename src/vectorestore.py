from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

import chromadb

# Load environment variables
load_dotenv()
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password))


def fetch_connections_from_graph(your_name):
    with driver.session() as session:
        result = session.run("""
            MATCH (me:Person {name: $your_name})-[:CONNECTED_TO]->(p:Person)
            RETURN p.name AS name, p.company AS company, p.position AS position, p.url AS url
        """, your_name=your_name)
        data = result.data()
        return pd.DataFrame(data)


def create_and_store_embeddings(df, persist_dir="chroma_store"):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=persist_dir)
    # client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
    collection = client.get_or_create_collection("linkedin_connections")

    for idx, row in df.iterrows():
        text_to_embed = f"{row['position']} at {row['company']}"
        embedding = model.encode(text_to_embed).tolist()

        collection.add(
            ids=[str(idx)],
            embeddings=[embedding],
            metadatas=[{
                "name": row["name"],
                "company": row["company"],
                "position": row["position"],
                "url": row["url"]
            }],
            documents=[text_to_embed]
        )
    # client.persist()
    print("✅ Embeddings stored successfully in ChromaDB!")


if __name__ == "__main__":
    your_name = "Atharva Chouthai"
    df = fetch_connections_from_graph(your_name)
    print(f"✅ Fetched {len(df)} connections from Neo4j.")
    create_and_store_embeddings(df)
