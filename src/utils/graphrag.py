import os
import openai
import numpy as np
from neo4j import GraphDatabase
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")

# Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Embedding model
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_model)

def get_connections_by_degree(your_name: str, degree: int, company=None, role=None):
    query = f"""
        MATCH (you:Person {{name: $your_name}})-[:CONNECTED_TO*1..{degree}]-(p:Person)
    """
    where_clauses = []
    if company:
        where_clauses.append("toLower(p.company) CONTAINS toLower($company)")
    if role:
        where_clauses.append("toLower(p.position) CONTAINS toLower($role)")
    if where_clauses:
        query += "WHERE " + " AND ".join(where_clauses) + "\n"
    query += """
        RETURN DISTINCT p.name AS name, p.company AS company, p.position AS position
    """
    with driver.session() as session:
        result = session.run(query, your_name=your_name, company=company, role=role)
        return result.data()

def load_prompt():
    return """
    You are a helpful AI that extracts structured intent from the user's question about their LinkedIn network.

    The user query is: {{query}}

    Only respond with a single JSON object using this format:
    {
      "role": "<job role the user is referring to or null if not provided>",
      "degree": <1, 2, 3, or null>,
      "companies": ["<company 1>", "<company 2>", ...] or [] if none
    }

    Do not include any other explanation or text.
    Do not say "Here is the JSON" or anything else.
    Respond with only the JSON object and nothing more.
    """

def find_similar_people(description, all_people, top_n=10):
    if not all_people:
        return []
    user_embedding = embedding_model.embed_query(description)
    texts = [f"{p['name']} {p['position']} {p['company']}" for p in all_people]
    person_embeddings = embedding_model.embed_documents(texts)
    similarities = cosine_similarity([user_embedding], person_embeddings)[0] * 100
    scored_people = []
    for idx, person in enumerate(all_people):
        scored_people.append({
            **person,
            "similarity": round(similarities[idx], 2)
        })
    scored_people.sort(key=lambda x: x["similarity"], reverse=True)
    unique_people = {}
    for person in scored_people:
        if person["name"] not in unique_people:
            unique_people[person["name"]] = person
    return list(unique_people.values())[:top_n]

def parse_query_with_groq(user_query):
    url = "https://api.groq.com/openai/v1/chat/completions"
    prompt_template = load_prompt()
    prompt = prompt_template.replace("{{query}}", user_query)
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY_2')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content'].strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing Llama response: {e}")
        print(content)
        raise

def graph_rag_query(your_name: str, user_query: str):
    print(f"\n🔎 Running GraphRAG Query for: {user_query} (querying all degrees)")
    parsed_query = parse_query_with_groq(user_query)
    companies = parsed_query.get("companies", [])
    role = parsed_query.get("role")
    is_structured = bool(role or (companies and any(companies)))

    degrees = [1, 2, 3]
    all_results = []

    if is_structured:
        if not companies:
            companies = [None]
        for company in companies:
            for degree in degrees:
                graph_results = get_connections_by_degree(your_name, degree, company, role)
                if not graph_results:
                    print(f"⚠️ No connections found for {degree}° degree for company: {company or 'Any'}")
                    continue
                query_embedding = embedding_model.embed_query(user_query)
                texts = [f"{p['name']} {p['position']} {p['company']}" for p in graph_results]
                person_embeddings = embedding_model.embed_documents(texts)
                similarities = cosine_similarity([query_embedding], person_embeddings)[0] * 100
                for idx, person in enumerate(graph_results):
                    sim_score = round(similarities[idx], 2)
                    hybrid_score = round(0.7 * sim_score + 0.3 * (30 - degree), 2)
                    all_results.append({
                        **person,
                        "similarity": sim_score,
                        "hybrid_score": hybrid_score,
                        "degree": degree
                    })
        unique_results = {p['name']: p for p in all_results}
        unique_graph_results = list(unique_results.values())
        if unique_graph_results:
            print(f"\n📢 Top Matches in your network (across all degrees):\n")
            for person in unique_graph_results:
                print(f"{person['name']} - {person['position']} @ {person['company']}")
                print(f"Similarity Score: {person['similarity']}% | Hybrid Score: {person['hybrid_score']}")
                print("-" * 50)
            return unique_graph_results

    # Fallback to semantic search if unstructured query or no results
    print("⚠️ No direct matches found or unstructured query. Trying semantic similarity fallback...")
    fallback_people = []
    for degree in degrees:
        results = get_connections_by_degree(your_name, degree, company=None, role=None)
        for r in results:
            r["degree"] = degree
        fallback_people.extend(results)
    if fallback_people:
        similar_people = find_similar_people(user_query, fallback_people, top_n=10)
        print(f"\n📌 Top Semantic Matches (based on your interests):\n")
        for person in similar_people:
            print(f"{person['name']} - {person['position']} @ {person['company']}")
            print(f"🔗 Similarity Score: {person['similarity']}%")
            print("-" * 50)
        return similar_people
    else:
        print("⚠️ No people in your network to compare for similarity.")
        return []

if __name__ == "__main__":
    your_name = input("Enter your name: ")
    query = input("Enter your query (e.g., 'Find Data Scientists' or 'Who works at ZS Associates'): ")
    graph_rag_query(your_name, query)