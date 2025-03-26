import os
import json
import re
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase
from jsearch_api import get_jobs_for_company_and_role

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

PROMPT_PATH = os.path.join(os.path.dirname(__file__), '/Users/atharvachouthai/Desktop/LinkedIn Rag/src/prompts/query_parser_prompt.txt')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def load_prompt():
    with open(PROMPT_PATH, 'r') as file:
        return file.read()

def parse_query_with_groq(user_query):
    url = "https://api.groq.com/openai/v1/chat/completions"

    prompt = f"""
    The user asked: \"{user_query}\".
    Respond ONLY with a single JSON object that contains:
    {{
        "role": <inferred role or None>,
        "degree": <1, 2, 3, or None>,
        "company": <company name or None>
    }}.
    Do NOT add any explanation or text outside this JSON object.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    content = response.json()['choices'][0]['message']['content'].strip()

    match = re.search(r"\{.*?\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e:
            print("⚠️ JSON parsing error:", e)
            print("🔎 Raw content received:\n", content)
            raise
    else:
        print("❌ Couldn't find a valid JSON block in the response:")
        print(content)
        raise ValueError("No JSON found in LLM response.")

def get_people_from_graph(company, degree):
    with driver.session() as session:
        query = f"""
            MATCH (me:Person {{name: 'Atharva Chouthai'}})-[:CONNECTED_TO*1..{degree or 3}]-(p:Person)
            WHERE p.company CONTAINS '{company}'
            RETURN p.name AS name, p.position AS position, p.company AS company, 
                   coalesce(p.linkedin, 'Not available') AS url
            LIMIT 10
        """
        results = session.run(query)
        return results.data()

def show_jobs_if_user_wants(company, role):
    ask = input(f"\n🧠 Would you like to see open roles at {company}? (yes/no): ").strip().lower()
    if ask == 'yes':
        print(f"\n🧠 Checking for open roles at {company}...\n")
        job_listings = get_jobs_for_company_and_role(company, role if role else "hiring")
        if job_listings:
            print(f"✅ Top job listings at {company}:")
            for job in job_listings:
                print(f"- {job['job_title']} in {job['job_city']}, {job['job_state']}")
                print(f"  Posted: {job['job_posted_at_datetime_utc']}")
                print(f"  🔗 Apply here: {job['job_apply_link']}")
                print("-" * 40)
        else:
            print(f"ℹ️ No current listings found for {company}.")
    else:
        print("👍 Okay, no job listings fetched.")

def run_dynamic_graph_query(parsed_query):
    role = parsed_query.get("role")
    degree = parsed_query.get("degree")
    company = parsed_query.get("company")

    if not company:
        print("❗ You must specify a company to search your network.")
        return

    print(f"\n➡️ Interpreted query:\nRole: {role}, Degree: {degree}, Company: {company}")
    print(f"\n🔎 Finding people in your network working at {company}...\n")

    try:
        people = get_people_from_graph(company, degree)

        if people:
            print(f"✅ People in your {degree or 'all'}° network at {company}:")
            for person in people:
                print(f"👉 {person['name']} - {person['position']} @ {person['company']}")
                print(f"🔗 LinkedIn: {person['url']}")
                print("-" * 40)

            show_jobs_if_user_wants(company, role)
        else:
            print(f"⚠️ No people in your network work at {company}.")

    except Exception as e:
        print(f"⚠️ Error running Neo4j query: {e}")
