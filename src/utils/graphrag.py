# import os
# import openai
# from dotenv import load_dotenv
# from neo4j import GraphDatabase
# from langchain_community.embeddings import OpenAIEmbeddings
# from langchain.vectorstores import Chroma
# from sklearn.metrics.pairwise import cosine_similarity
# from typing import List, Dict
# import numpy as np

# load_dotenv()

# # Load ENV
# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

# # Neo4j connection
# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# # OpenAI Embedding Model
# embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# # Chroma Vector Store
# vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_model)


# def get_connections_by_degree(your_name: str, degree: int) -> List[Dict]:
#     with driver.session() as session:
#         query = f"""
#             MATCH (you:Person {{name: $your_name}})-[:CONNECTED_TO*1..{degree}]-(p:Person)
#             RETURN DISTINCT p.name AS name, p.company AS company, p.position AS position, 
#                    coalesce(p.linkedin, 'Unknown') AS url
#         """
#         result = session.run(query, your_name=your_name)
#         people = result.data()
#         print(f"\n✅ Raw results from Neo4j: {len(people)} connections")
#         return people


# def graphrag_query(your_name: str, user_query: str, degree: int = 2):
#     print(f"\n🔎 Running GraphRAG Query for: {user_query} (within {degree}° connections)")

#     graph_results = get_connections_by_degree(your_name, degree)
#     if not graph_results:
#         print("⚠️ No graph connections found.")
#         return []

#     query_embedding = np.array(embedding_model.embed_query(user_query)).reshape(1, -1)

#     enriched_results = []
#     for person in graph_results:
#         # Construct document string
#         text = f"{person['name']} is a {person['position']} at {person['company']}"
#         doc_embedding = np.array(embedding_model.embed_query(text)).reshape(1, -1)

#         # Cosine similarity
#         similarity = cosine_similarity(query_embedding, doc_embedding)[0][0]
#         similarity_percent = round(similarity * 100, 2)

#         hybrid_score = round(similarity_percent + (30 - (degree - 1) * 5), 2)  # weightage
#         person.update({
#             "similarity_score": similarity_percent,
#             "degree": degree,
#             "hybrid_score": hybrid_score
#         })
#         enriched_results.append(person)

#     sorted_results = sorted(enriched_results, key=lambda x: x["hybrid_score"], reverse=True)

#     print(f"\n📢 Top Matches in your {degree}° network:\n")
#     for match in sorted_results[:50]:
#         print(f"{match['name']} - {match['position']} @ {match['company']}")
#         print(f"LinkedIn: {match['url']}")
#         print(f"Similarity Score: {match['similarity_score']}% | Connection Degree: {match['degree']}° | Hybrid Score: {match['hybrid_score']}")
#         print("-" * 50)

#     return sorted_results


# # CLI Entry Point
# if __name__ == "__main__":
#     your_name = input("Enter your name: ")
#     query = input("Enter your query (e.g., 'Find Data Scientists'): ")
#     degree = int(input("Enter degree of connection to search (1 / 2 / 3): "))
#     graphrag_query(your_name, query, degree)

# import os
# import openai
# import numpy as np
# from neo4j import GraphDatabase
# from langchain_community.vectorstores import Chroma
# # from langchain_openai import OpenAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings
# from dotenv import load_dotenv
# from sklearn.metrics.pairwise import cosine_similarity

# load_dotenv()

# # Load env variables
# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USER = os.getenv("NEO4J_USER")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")

# # Initialize Neo4j driver
# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# # Initialize vectorstore and embedding model
# embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
# vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_model)

# def get_connections_by_degree(your_name: str, degree: int):
#     query = f"""
#         MATCH (you:Person {{name: $your_name}})-[:CONNECTED_TO*1..{degree}]-(p:Person)
#         RETURN DISTINCT p.name AS name, p.company AS company, p.position AS position, 
#                coalesce(p.linkedin, 'Unknown') AS url
#     """
#     with driver.session() as session:
#         result = session.run(query, your_name=your_name)
#         return result.data()

# # def graph_rag_query(your_name: str, user_query: str, degree: int):
# #     print(f"\n🔎 Running GraphRAG Query for: {user_query} (within {degree}° connections)")
# #     graph_results = get_connections_by_degree(your_name, degree)
# #     print(f"\n✅ Raw results from Neo4j: {len(graph_results)} connections")

# #     if not graph_results:
# #         print("No data from graph.")
# #         return []

# #     from sklearn.metrics.pairwise import cosine_similarity
# #     import numpy as np

# #     # Step 1: Embed the user query
# #     query_embedding = embedding_model.embed_query(user_query)

# #     # Step 2: Prepare all person descriptions
# #     texts = [
# #         f"{p['name']} {p['position']} {p['company']}" for p in graph_results
# #     ]

# #     # Step 3: Batch embed all at once
# #     person_embeddings = embedding_model.embed_documents(texts)

# #     # Step 4: Compute cosine similarities in one shot
# #     similarities = cosine_similarity(
# #         [query_embedding], person_embeddings
# #     )[0] * 100  # Scale to % if desired

# #     # Step 5: Attach scores to each person
# #     scored_results = []
# #     for idx, person in enumerate(graph_results):
# #         sim_score = round(similarities[idx], 2)
# #         hybrid_score = round(0.7 * sim_score + 0.3 * (30 - degree), 2)

# #         scored_results.append({
# #             **person,
# #             "similarity": sim_score,
# #             "hybrid_score": hybrid_score,
# #             "degree": degree
# #         })

# #     # Step 6: Sort and display
# #     scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

# #     print(f"\n📢 Top Matches in your {degree}° network:\n")
# #     for person in scored_results[:25]:  # Show top 25
# #         print(f"{person['name']} - {person['position']} @ {person['company']}")
# #         print(f"LinkedIn: {person['url']}")
# #         print(f"Similarity Score: {person['similarity']}% | Connection Degree: {degree}° | Hybrid Score: {person['hybrid_score']}")
# #         print("-" * 50)

# def graph_rag_query(your_name: str, user_query: str, degree: int):
#     # Ensure degree is set to a valid value (default to 2 if not provided)
#     if degree is None:
#         degree = 2  # Default to 2 degrees if None is passed

#     print(f"\n🔎 Running GraphRAG Query for: {user_query} (within {degree}° connections)")
    
#     # Make sure that degree is passed correctly
#     graph_results = get_connections_by_degree(your_name, degree)
#     print(f"\n✅ Raw results from Neo4j: {len(graph_results)} connections")

#     if not graph_results:
#         print("No data from graph.")
#         return []

#     from sklearn.metrics.pairwise import cosine_similarity
#     import numpy as np

#     # Step 1: Embed the user query
#     query_embedding = embedding_model.embed_query(user_query)

#     # Step 2: Prepare all person descriptions
#     texts = [
#         f"{p['name']} {p['position']} {p['company']}" for p in graph_results
#     ]

#     # Step 3: Batch embed all at once
#     person_embeddings = embedding_model.embed_documents(texts)

#     # Step 4: Compute cosine similarities in one shot
#     similarities = cosine_similarity(
#         [query_embedding], person_embeddings
#     )[0] * 100  # Scale to % if desired

#     # Step 5: Attach scores to each person
#     scored_results = []
#     for idx, person in enumerate(graph_results):
#         sim_score = round(similarities[idx], 2)
#         hybrid_score = round(0.7 * sim_score + 0.3 * (30 - degree), 2)

#         scored_results.append({
#             **person,
#             "similarity": sim_score,
#             "hybrid_score": hybrid_score,
#             "degree": degree
#         })

#     # Step 6: Sort and display
#     scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

#     print(f"\n📢 Top Matches in your {degree}° network:\n")
#     for person in scored_results[:25]:  # Show top 25
#         print(f"{person['name']} - {person['position']} @ {person['company']}")
#         print(f"LinkedIn: {person['url']}")
#         print(f"Similarity Score: {person['similarity']}% | Connection Degree: {degree}° | Hybrid Score: {person['hybrid_score']}")
#         print("-" * 50)

# if __name__ == "__main__":
#     your_name = input("Enter your name: ")
#     query = input("Enter your query (e.g., 'Find Data Scientists'): ")
#     degree = int(input("Enter degree of connection to search (1 / 2 / 3): "))

#     graph_rag_query(your_name, query, degree)

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

# Load environment variables
load_dotenv()

# Load env variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Initialize vectorstore and embedding model
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_model)

def get_connections_by_degree(your_name: str, degree: int, company=None, role=None):
    # Build the query based on available parameters
    query = f"""
        MATCH (you:Person {{name: $your_name}})-[:CONNECTED_TO*1..{degree}]-(p:Person)
        """
    
    # Add condition for company if provided
    if company:
        query += "WHERE p.company CONTAINS $company "
    
    # Add condition for role if provided
    if role:
        query += "AND p.position CONTAINS $role "
    
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
      "company": "<company name if mentioned, or null>"
    }
    
    Do not include any other explanation or text.
    Do not say "Here is the JSON" or anything else.
    Respond with only the JSON object and nothing more.
    """

def parse_query_with_groq(user_query):
    url = "https://api.groq.com/openai/v1/chat/completions"
    prompt_template = load_prompt()
    prompt = prompt_template.replace("{{query}}", user_query)

    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",  # Adjust model based on availability
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
    company = parsed_query.get("company")
    role = parsed_query.get("role")
    
    degrees = [1, 2, 3]  # Query all degrees for comprehensive results
    all_results = []

    for degree in degrees:
        graph_results = get_connections_by_degree(your_name, degree, company, role)
        if not graph_results:
            print(f"⚠️ No connections found for {degree}° degree.")
            continue

        query_embedding = embedding_model.embed_query(user_query)

        texts = [f"{p['name']} {p['position']} {p['company']}" for p in graph_results]

        person_embeddings = embedding_model.embed_documents(texts)

        similarities = cosine_similarity([query_embedding], person_embeddings)[0] * 100

        scored_results = []
        for idx, person in enumerate(graph_results):
            sim_score = round(similarities[idx], 2)
            hybrid_score = round(0.7 * sim_score + 0.3 * (30 - degree), 2)

            scored_results.append({
                **person,
                "similarity": sim_score,
                "hybrid_score": hybrid_score,
                "degree": degree
            })

        scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        all_results.extend(scored_results[:25])

    # Remove duplicates based on name
    unique_results = {person['name']: person for person in all_results}
    unique_graph_results = list(unique_results.values())

    if unique_graph_results:
        print(f"\n📢 Top Matches in your network (across all degrees):\n")
        for person in unique_graph_results:
            print(f"{person['name']} - {person['position']} @ {person['company']}")
            # print(f"LinkedIn: {person['url']}")
            print(f"Similarity Score: {person['similarity']}% | Hybrid Score: {person['hybrid_score']}")
            print("-" * 50)
    else:
        print("⚠️ No connections found in your network matching the query.")

    return unique_graph_results

if __name__ == "__main__":
    your_name = input("Enter your name: ")
    query = input("Enter your query (e.g., 'Find Data Scientists' or 'Who works at ZS Associates'): ")

    graph_rag_query(your_name, query)