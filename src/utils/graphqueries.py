import os
import requests
from dotenv import load_dotenv
from graphrag import graph_rag_query
from graphrag import parse_query_with_groq

load_dotenv()

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