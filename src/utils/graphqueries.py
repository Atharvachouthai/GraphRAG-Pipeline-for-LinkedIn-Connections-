# import os
# import json
# import re
# import requests
# import streamlit as st
# from dotenv import load_dotenv
# from neo4j import GraphDatabase
# from jsearch_api import get_jobs_for_company_and_role
# from fuzzywuzzy import fuzz

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USER = os.getenv("NEO4J_USER")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# PROMPT_PATH = os.path.join(os.path.dirname(__file__), '../prompts/query_parser_prompt.txt')

# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# def load_prompt():
#     with open(PROMPT_PATH, 'r') as file:
#         return file.read()

# def parse_query_with_groq(user_query):
#     url = "https://api.groq.com/openai/v1/chat/completions"
#     prompt_template = load_prompt()
#     prompt = prompt_template.replace("{{query}}", user_query)

#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": "llama3-8b-8192",
#         "messages": [
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.2,
#         "max_tokens": 300
#     }

#     response = requests.post(url, headers=headers, json=payload)
#     response.raise_for_status()
#     content = response.json()['choices'][0]['message']['content'].strip()

#     match = re.search(r"\{[\s\S]*?\}", content)
#     if match:
#         try:
#             return json.loads(match.group(0))
#         except json.JSONDecodeError as e:
#             st.error(f"⚠️ JSON parsing error: {e}")
#             st.code(content)
#             raise
#     else:
#         st.error("❌ Couldn't find a valid JSON block in the response:")
#         st.code(content)
#         raise ValueError("No JSON found in LLM response.")

# def get_people_from_graph(company, degree, streamlit=False):
#     with driver.session() as session:
#         query = f"""
#             MATCH (me:Person {{name: 'Atharva Chouthai'}})-[:CONNECTED_TO*1..{degree or 3}]-(p:Person)
#             WHERE p.company CONTAINS '{company}'
#             RETURN p.name AS name, p.position AS position, p.company AS company, 
#                    coalesce(p.linkedin, 'Not available') AS url
#             LIMIT 10
#         """
#         results = session.run(query)
#         data = results.data()

#         if streamlit:
#             if data:
#                 st.subheader(f"📠 Finding people at {company}...")
#                 for person in data:
#                     st.markdown(f"👉 **{person['name']}** - {person['position']} @ {person['company']}")
#                     st.markdown(f"🔗 LinkedIn: {person['url']}")
#                     st.divider()
#             else:
#                 st.warning(f"⚠️ No one from your network works at {company}.")
#         else:
#             print("\n🧪 Raw Neo4j results:")
#             print(data)
#             if data:
#                 print(f"\n✅ People in your {degree or 'all'}° network at {company}:")
#                 for person in data:
#                     print(f"👉 {person['name']} - {person['position']} @ {person['company']}")
#                     print(f"🔗 LinkedIn: {person['url']}")
#                     print("-" * 40)
#             else:
#                 print(f"⚠️ No one from your network works at {company}.")

# def show_jobs_for_streamlit(company, role):
#     job_listings = get_jobs_for_company_and_role(company, role if role else "hiring")
#     if job_listings:
#         for job in job_listings:
#             st.markdown(f"- **{job['job_title']}** in {job['job_city']}, {job['job_state']}")
#             st.markdown(f"  Posted: {job['job_posted_at_datetime_utc']}")
#             st.markdown(f"  🔗 [Apply here]({job['job_apply_link']})")
#             st.divider()
#     else:
#         st.info(f"ℹ️ No current listings found for {company}.")

# def run_dynamic_graph_query(parsed_query, streamlit=False):
#     role = parsed_query.get("role")
#     degree = parsed_query.get("degree")
#     company = parsed_query.get("company")

#     if degree not in [1, 2, 3, None]:
#         msg = "⚠️ Degree must be 1, 2, or 3."
#         st.warning(msg) if streamlit else print(msg)
#         return

#     if not company:
#         msg = "❗ You must specify a company to search your network."
#         st.warning(msg) if streamlit else print(msg)
#         return

#     if streamlit:
#         st.subheader(f"🔎 Finding people in your network working at {company}...")
#     else:
#         print(f"\n🔎 Finding people in your network working at {company}...\n")

#     get_people_from_graph(company, degree, streamlit=streamlit)

#     if streamlit:
#         if st.toggle(f"🔎 Show jobs at {company}", key=f"jobs_{company}"):
#             show_jobs_for_streamlit(company, role)
#     else:
#         ask = input(f"\n🧠 Would you like to see open roles at {company}? (yes/no): ").strip().lower()
#         if ask == 'yes':
#             print(f"\n🧠 Checking for open roles at {company}...\n")
#             show_jobs_for_streamlit(company, role)

# def find_similar_people(role, degree):
#     with driver.session() as session:
#         query = f"""
#             MATCH (me:Person {{name: 'Atharva Chouthai'}})-[:CONNECTED_TO*1..{degree or 3}]-(p:Person)
#             RETURN p.name AS name, p.position AS position, p.company AS company, 
#                    coalesce(p.linkedin, 'Not available') AS url
#         """
#         results = session.run(query)
#         all_people = results.data()

#     ranked = []
#     for person in all_people:
#         similarity = fuzz.partial_ratio(role.lower(), person['position'].lower())
#         person['similarity'] = similarity
#         ranked.append(person)

#     return sorted(ranked, key=lambda x: x['similarity'], reverse=True)[:5]

import os
import requests
from dotenv import load_dotenv
from graphrag import graph_rag_query
from graphrag import parse_query_with_groq

load_dotenv()

# Adzuna API keys
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

def run_adzuna_job_search(role, location, company=None, level=None, max_results=5):
    country = "us"
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

    query = f"{role}"
    if level:
        query += f" {level}"
    if company:
        query += f" {company}"

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": max_results,
        "what": query,
        "where": location,
        "content-type": "application/json"
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200 and "results" in data:
        return [{
            "title": job["title"],
            "company": job["company"]["display_name"],
            "location": job["location"]["display_name"],
            "url": job["redirect_url"]
        } for job in data["results"]]
    else:
        return []

def run_workflow():
    # Get user input
    your_name = input("Enter your name: ")
    query = input("Enter your query (e.g., 'Find Data Scientists'): ")

    # Parse the user query to extract role, location, company, etc.
    parsed_query = parse_query_with_groq(query)

    role = parsed_query.get("role")
    company = parsed_query.get("company")

    # Call graph_rag_query to fetch people
    graph_results = graph_rag_query(your_name, query)

    if not graph_results:
        print("No people found in your network.")
        return

    print("\n📢 Top Matches in your network:")
    for person in graph_results:
        print(f"{person['name']} - {person['position']} @ {person['company']}")
        print(f"LinkedIn: {person['url']}")
        print("-" * 50)

    # Ask the user if they want to search for job openings at the specified company
    if company:
        search_jobs = input(f"Do you want to see job openings at {company}? (yes/no): ")
        if search_jobs.lower() == "yes":
            location = input(f"Enter the location for jobs at {company}: ")
            jobs = run_adzuna_job_search(role, location, company=company)

            if jobs:
                print(f"\n🚀 Job Listings for '{role}' at {company}:")
                for job in jobs:
                    print(f"🔹 **{job['title']}** at *{job['company']}*")
                    print(f"📍 {job['location']}")
                    print(f"🔗 [Apply here]({job['url']})")
                    print("-" * 50)
            else:
                print("No job openings found.")
        else:
            print("Okay, no job search will be done.")
    else:
        print("No company provided for job search.")

if __name__ == "__main__":
    run_workflow()