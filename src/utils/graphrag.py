import os
import json
import openai
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
import requests
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_URI = os.getenv("NEO4J_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
Chroma_DIR = os.getenv("CHROMA_DIR", "chroma_db")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(persist_directory=Chroma_DIR, embedding_function=embedding_model)


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
        You are a helpful AI that extracts structured entities (roles, companies, degrees) from a user's question about their LinkedIn network.

        Your goal is to return a JSON object with:
        - roles: list of role keywords or job titles (e.g., "Recruiter", "Data Scientist", "ML Engineer")
        - companies: list of company names
        - degree: connection degree (1, 2, or 3) if mentioned, else null

        Respond with only the JSON. Do NOT include extra text or commentary.

        Here are a few examples:

        ---

        User: Who works at Google?
        → {"roles": [], "companies": ["Google"], "degree": null}

        User: Who are the data scientists in my 2nd degree network?
        → {"roles": ["Data Scientist"], "companies": [], "degree": 2}

        User: I want to find ML engineers and researchers at Meta or Amazon.
        → {"roles": ["ML Engineer", "Researcher"], "companies": ["Meta", "Amazon"], "degree": null}

        User: Show me recruiters, talent scouts, or hiring managers in my network.
        → {"roles": ["Recruiter", "Talent Scout", "Hiring Manager"], "companies": [], "degree": null}

        User: I’m a machine learning enthusiast looking for people in AI, data, or ML roles.
        → {"roles": ["AI", "Data", "Machine Learning"], "companies": [], "degree": null}

        ---

        Now do the same for this:

        User: {{query}}
        →
        """


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
        print(f"❌ Error parsing LLM response: {e}")
        print(content)
        raise

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
    unique_people = {p['name']: p for p in scored_people}
    return list(unique_people.values())[:top_n]

def graph_rag_query(your_name: str, user_query: str):
    print(f"\n🔎 Running GraphRAG Query for: {user_query} (querying all degrees)")
    parsed_query = parse_query_with_groq(user_query)
    roles = parsed_query.get("roles", []) or []
    companies = parsed_query.get("companies", []) or []
    is_structured = bool(roles or companies)
    degrees = [1, 2, 3]
    all_results = []

    if is_structured:
        if not companies:
            companies = [None]
        if not roles:
            roles = [None]
        for role in roles:
            for company in companies:
                for degree in degrees:
                    graph_results = get_connections_by_degree(your_name, degree, company, role)
                    if not graph_results:
                        print(f"⚠️ No connections found for {degree}° degree for company: {company or 'Any'} and role: {role or 'Any'}")
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

    print("⚠️ No direct matches found or unstructured query. Trying semantic similarity fallback...")
    fallback_people = []
    for degree in degrees:
        results = get_connections_by_degree(your_name, degree)
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