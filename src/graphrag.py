from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password))


# def get_first_degree_connections(your_name):
#     with driver.session() as session:
#         result = session.run("""
#             MATCH (me:Person {name: $your_name})-[:CONNECTED_TO]->(p:Person)
#             RETURN p.name AS name, p.company AS company, p.position AS position, p.url AS url
#         """, your_name=your_name)
#         return result.data()

def get_connections_by_degree(your_name, degree=1):
    with driver.session() as session:
        if degree == 1:
            query = """
                MATCH (me:Person {name: $your_name})-[:CONNECTED_TO]->(p:Person)
                RETURN p.name AS name, p.company AS company, p.position AS position, p.url AS url
            """
        elif degree == 2:
            query = """
                MATCH (me:Person {name: $your_name})-[:CONNECTED_TO]->(:Person)-[:CONNECTED_TO]->(p:Person)
                RETURN DISTINCT p.name AS name, p.company AS company, p.position AS position, p.url AS url
            """
        elif degree == 3:
            query = """
                MATCH (me:Person {name: $your_name})-[:CONNECTED_TO*1..3]->(p:Person)
                RETURN DISTINCT p.name AS name, p.company AS company, p.position AS position, p.url AS url
            """
        else:
            raise ValueError("Degree can only be 1, 2, or 3 for now.")

        result = session.run(query, your_name=your_name)
        return result.data()


def query_chromadb(query_text, top_k=5, persist_dir="chroma_store"):
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection("linkedin_connections")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(query_text).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results


# def graphrag_query(your_name, user_query):
#     print(f"🔎 Running GraphRAG Query for: {user_query}")
#     graph_results = get_first_degree_connections(your_name)
#     vector_results = query_chromadb(user_query, top_k=10)

#     # Combine and filter vector results only for first-degree connections
#     first_degree_names = {res['name'] for res in graph_results}
#     matched = []
#     for idx, metadata in enumerate(vector_results['metadatas'][0]):
#         if metadata['name'] in first_degree_names:
#             matched.append({
#                 "name": metadata["name"],
#                 "company": metadata["company"],
#                 "position": metadata["position"],
#                 "url": metadata["url"],
#                 "score": vector_results['distances'][0][idx]
#             })

#     # Sort by score (closer is better)
#     matched = sorted(matched, key=lambda x: x["score"])

#     return matched

# def graphrag_query(your_name, user_query, degree=1):
#     print(f"🔎 Running GraphRAG Query for: {user_query} (within {degree}° connections)")
#     graph_results = get_connections_by_degree(your_name, degree)
#     vector_results = query_chromadb(user_query, top_k=20)

#     connection_names = {res['name'] for res in graph_results}
#     matched = []
#     for idx, metadata in enumerate(vector_results['metadatas'][0]):
#         if metadata['name'] in connection_names:
#             matched.append({
#                 "name": metadata["name"],
#                 "company": metadata["company"],
#                 "position": metadata["position"],
#                 "url": metadata["url"],
#                 "similarity_score": round((1 - vector_results['distances'][0][idx]) * 100, 2)  # convert to %
#             })

#     matched = sorted(matched, key=lambda x: -x["similarity_score"])  # sort by similarity descending
#     return matched

def degree_for_person(person_name, your_name):
    # Quickly determine the shortest path length between you and this person
    with driver.session() as session:
        result = session.run("""
            MATCH (start:Person {name: $your_name}), (end:Person {name: $person_name}),
            p = shortestPath((start)-[:CONNECTED_TO*..3]-(end))
            RETURN length(p) AS degree
        """, your_name=your_name, person_name=person_name)
        record = result.single()
        if record:
            # degree = path length / 2 (since it's undirected), clamp between 1 and 3
            return min(max((record["degree"] // 2), 1), 3)
        else:
            return 3  # fallback


def graphrag_query(your_name, user_query, degree=1):
    print(f"🔎 Running GraphRAG Query for: {user_query} (within {degree}° connections)")
    graph_results = get_connections_by_degree(your_name, degree)
    vector_results = query_chromadb(user_query, top_k=50)  # Increase top_k to get more candidates

    connection_data = {res['name']: res for res in graph_results}
    matched = []
    for idx, metadata in enumerate(vector_results['metadatas'][0]):
        name = metadata['name']
        if name in connection_data:
            # similarity_score = (1 - vector_results['distances'][0][idx]) * 100
            similarity_score = max(min((1 - vector_results['distances'][0][idx]) * 100, 100), 0)
            # Add hybrid score: prioritize closer graph degree
            connection_degree = degree_for_person(name, your_name)  # We'll add this helper next
            hybrid_score = (similarity_score * 0.7) + ((4 - connection_degree) * 10)  


            matched.append({
                "name": name,
                "company": metadata["company"],
                "position": metadata["position"],
                "url": metadata["url"],
                "similarity_score": round(similarity_score, 2),
                "degree": connection_degree,
                "hybrid_score": round(hybrid_score, 2)
            })

    matched = sorted(matched, key=lambda x: -x["hybrid_score"])
    return matched


if __name__ == "__main__":
    your_name = "Atharva Chouthai"
    query = input("Enter your query (e.g., 'Find Data Scientists'): ")
    degree = int(input("Enter degree of connection to search (1 / 2 / 3): "))
    
    results = graphrag_query(your_name, query, degree)
    
    print(f"\n📢 Top Matches in your {degree}° network:\n")
    for person in results:
        print(f"{person['name']} - {person['position']} @ {person['company']}")
        print(f"LinkedIn: {person['url']}")
        print(f"Similarity Score: {person['similarity_score']}% | Connection Degree: {person['degree']}° | Hybrid Score: {person['hybrid_score']}")
        print("-" * 50)

