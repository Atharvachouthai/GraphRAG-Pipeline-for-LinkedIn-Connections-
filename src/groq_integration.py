from utils.graphqueries import (
    parse_query_with_groq,
    get_people_from_graph,
    show_jobs_if_user_wants,
    run_dynamic_graph_query
)

def main():
    print("Welcome to LinkedIn GraphRAG 💼")

    while True:
        user_query = input("\nAsk me anything about your LinkedIn network (type 'exit' to quit): ")
        if user_query.lower() == 'exit':
            print("👋 Exiting... Goodbye!")
            break

        try:
            parsed_query = parse_query_with_groq(user_query)

            if isinstance(parsed_query, list):
                parsed_query = parsed_query[0]

            role = parsed_query.get("role")
            degree = parsed_query.get("degree")
            company = parsed_query.get("company")

            print(f"\n➡️ Interpreted query:\nRole: {role}, Degree: {degree}, Company: {company}")

            if company and not role:
                # If only company is provided, just fetch people
                get_people_from_graph(company, degree)
                # Ask user if they want to see openings
                show_jobs_if_user_wants(company, role)
            elif company and role:
                # If both company and role provided, run more dynamic query
                run_dynamic_graph_query(parsed_query)
            else:
                print("❗ Please provide at least a company name to search.")

        except Exception as e:
            print(f"⚠️ Error occurred: {e}")

if __name__ == "__main__":
    main()
