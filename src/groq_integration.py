# from utils.graphqueries import (
#     parse_query_with_groq,
#     get_people_from_graph,
#     show_jobs_if_user_wants,
#     run_dynamic_graph_query,
#     add_user_message,
#     add_ai_message
# )

# def main():
#     print("Welcome to LinkedIn GraphRAG 💼")

#     while True:
#         user_query = input("\nAsk me anything about your LinkedIn network (type 'exit' to quit): ")
#         if user_query.lower() == 'exit':
#             print("👋 Exiting... Goodbye!")
#             break

#         try:
#             add_user_message(user_query)
#             parsed_query = parse_query_with_groq(user_query)
#             add_ai_message(str(parsed_query))

#             if isinstance(parsed_query, list):
#                 parsed_query = parsed_query[0]

#             role = parsed_query.get("role")
#             degree = parsed_query.get("degree")
#             company = parsed_query.get("company")

#             print(f"\n➡️ Interpreted query:\nRole: {role}, Degree: {degree}, Company: {company}")

#             if company and not role:
#                 people = get_people_from_graph(company, degree)
#                 if people:
#                     print(f"\n✅ People in your {degree or 'all'}° network at {company}:")
#                     for person in people:
#                         print(f"👉 {person['name']} - {person['position']} @ {person['company']}")
#                         print(f"🔗 LinkedIn: {person['url']}")
#                         print("-" * 40)
#                 else:
#                     print("⚠️ No people found in your network.")
#                 show_jobs_if_user_wants(company, role)

#             elif company and role:
#                 run_dynamic_graph_query(parsed_query)

#             else:
#                 print("❗ Please provide at least a company name to search.")

#         except Exception as e:
#             print(f"⚠️ Error occurred: {e}")

# if __name__ == "__main__":
#     main()

from utils.graphqueries import (
    parse_query_with_groq,
    get_people_from_graph,
    show_jobs_if_user_wants,
    run_dynamic_graph_query,
    find_similar_people
)
from utils.memory import (
    add_user_message,
    add_ai_message,
    get_memory_messages
)
import json

def main():
    print("Welcome to LinkedIn GraphRAG 💼")

    while True:
        user_query = input("\nAsk me anything about your LinkedIn network (type 'exit' to quit): ")
        if user_query.lower() == 'exit':
            print("👋 Exiting... Goodbye!")
            break

        # Track messages for memory
        add_user_message(user_query)

        try:
            parsed_query = parse_query_with_groq(user_query)

            if isinstance(parsed_query, list):
                parsed_query = parsed_query[0]

            role = parsed_query.get("role")
            degree = parsed_query.get("degree")
            company = parsed_query.get("company")

            print(f"\n➡️ Interpreted query:\nRole: {role}, Degree: {degree}, Company: {company}")
            add_ai_message(json.dumps(parsed_query))

            # --- Branch: Similar Role Discovery ---
            if role and not company and "similar" in user_query.lower():
                find_similar_people(role, degree)
                continue  # Go to next question

            # --- Branch: Dynamic Query (People + Jobs) ---
            if company and role:
                run_dynamic_graph_query(parsed_query)

            # --- Branch: People only (no role specified) ---
            elif company and not role:
                get_people_from_graph(company, degree)
                show_jobs_if_user_wants(company, role)

            else:
                print("❗ Please provide at least a company name or role to search.")

        except Exception as e:
            print(f"⚠️ Error occurred: {e}")

if __name__ == "__main__":
    main()
