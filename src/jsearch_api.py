import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')


def get_jobs_for_company_and_role(company, role="hiring", country="us", limit=5):
    url = "https://jsearch.p.rapidapi.com/search"

    querystring = {
        "query": f"{role} jobs at {company}",
        "page": "1",
        "num_pages": "1",
        "country": country,
        "date_posted": "all"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        jobs = response.json().get("data", [])

        return jobs[:limit]  # return only top 5 results

    except Exception as e:
        print(f"⚠️ Error fetching jobs for {company}: {e}")
        return []


if __name__ == "__main__":
    company_input = input("Enter company name: ")
    role_input = input("Enter role (or leave blank for generic 'hiring'): ") or "hiring"

    jobs = get_jobs_for_company_and_role(company_input, role_input)

    if jobs:
        print(f"✅ Showing top {len(jobs)} jobs at {company_input}:")
        for job in jobs:
            print(f"- {job['job_title']} at {job['employer_name']} ({job['job_city']}, {job['job_state']})")
            print(f"  Posted: {job['job_posted_at_datetime_utc']}")
            print(f"  Apply here: {job['job_apply_link']}")
            print("-" * 50)
    else:
        print(f"ℹ️ No active job postings found for {company_input}.")
