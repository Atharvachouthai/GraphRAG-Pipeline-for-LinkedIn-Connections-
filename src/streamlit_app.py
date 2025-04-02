# import streamlit as st
# from utils.graphqueries import (
#     parse_query_with_groq,
#     get_people_from_graph,
#     run_dynamic_graph_query,
#     show_jobs_for_streamlit
# )
# from utils.memory import (
#     add_user_message,
#     add_ai_message,
#     get_memory_messages
# )
# import json

# st.set_page_config(page_title="LinkedIn GraphRAG", layout="wide")

# # --- Sidebar: Conversation Memory ---
# st.sidebar.title("🧠 Conversation Memory")
# messages = get_memory_messages()
# for msg in messages:
#     role = "User" if msg.type == "human" else "AI"
#     st.sidebar.markdown(f"**{role}:** {msg.content}")

# # --- Main Title ---
# st.title("💼 LinkedIn GraphRAG")

# st.success("✅ Streamlit app is running correctly!")

# # --- User Input ---
# user_query = st.text_input("Ask something about your LinkedIn network:", "")

# if user_query:
#     st.markdown(f"🔍 You asked: **{user_query}**")

#     # Add to memory
#     add_user_message(user_query)

#     try:
#         parsed_query = parse_query_with_groq(user_query)

#         if isinstance(parsed_query, list):
#             parsed_query = parsed_query[0]

#         role = parsed_query.get("role")
#         degree = parsed_query.get("degree")
#         company = parsed_query.get("company")

#         st.markdown(
#             f"#### 🧠 Interpreted Query ➜ "
#             f"**Role:** `{role or 'None'}`, **Degree:** `{degree or 'None'}`, **Company:** `{company or 'None'}`"
#         )

#         add_ai_message(json.dumps(parsed_query))

#         # --- Logic: Handle query types ---
#         if role and not company and "similar" in user_query.lower():
#             st.subheader("🔍 Finding people with similar roles...")
#             from utils.graphqueries import find_similar_people
#             matches = find_similar_people(role, degree)
#             if matches:
#                 for person in matches:
#                     st.markdown(
#                         f"👉 **{person['name']}** - {person['position']} @ {person['company']} "
#                         f"(Similarity: {person['similarity']}%)"
#                     )
#                     st.markdown(f"🔗 [LinkedIn]({person['url']})" if person["url"] != "Not available" else "🔗 LinkedIn: Not available")
#                     st.divider()
#                     if st.toggle(f"💼 Show jobs at {person['company']}", key=f"jobs_{person['company']}"):
#                         show_jobs_for_streamlit(person["company"], role)
#             else:
#                 st.warning("⚠️ No similar people found in your network.")

#         elif company and role:
#             run_dynamic_graph_query(parsed_query, streamlit=True)

#         elif company and not role:
#             st.subheader(f"🔎 Finding people in your network working at {company}...")
#             get_people_from_graph(company, degree, streamlit=True)
#             if st.toggle(f"💼 Show jobs at {company}", key=f"jobs_{company}_people_only"):
#                 show_jobs_for_streamlit(company, role)

#         else:
#             st.info("ℹ️ Please provide at least a company name or a role to continue.")

#     except Exception as e:
#         st.error(f"❌ Error: {e}")

# import streamlit as st
# from utils.graphrag import graph_rag_query

# st.set_page_config(page_title="GraphRAG Network Explorer", layout="centered")
# st.title("🔗 LinkedIn Network Search")

# # Input fields
# your_name = st.text_input("Enter your name")
# query = st.text_input("Enter your query (e.g., 'Who works at Google?')")

# # Button to trigger search
# if st.button("🔍 Search your Network"):
#     if your_name and query:
#         with st.spinner("Analyzing your network using GraphRAG..."):
#             results = graph_rag_query(your_name, query)

#         if not results:
#             st.warning("⚠️ No connections found in your network matching the query.")
#         else:
#             st.subheader("📢 Top Matches in Your Network")
#             for person in results:
#                 st.markdown(f"**👉 {person['name']}** - {person['position']} @ {person['company']}")
#                 st.markdown(f"🔗 LinkedIn: {person.get('url', 'Unknown')}")
#                 st.markdown(f"📈 Similarity Score: `{person['similarity']}%` | Hybrid Score: `{person['hybrid_score']}`")
#                 st.markdown("---")
#     else:
#         st.error("Please enter both your name and query to proceed.")

import streamlit as st
from utils.graphrag import graph_rag_query

st.set_page_config(page_title="LinkedIn GraphRAG", layout="centered")
st.title("🔗 LinkedIn Network Search")

# User input
your_name = st.text_input("Enter your name:")
user_query = st.text_input("Enter your query (e.g., 'Who works at ZS Associates'):") 

# Trigger network search
if st.button("Search Network"):
    if your_name and user_query:
        with st.spinner("Analyzing your network using GraphRAG..."):
            results = graph_rag_query(your_name, user_query)

        if not results:
            st.warning("⚠️ No connections found in your network matching the query.")
        else:
            st.subheader("📢 Top Matches in Your Network")
            for person in results:
                st.markdown(f"**👉 {person['name']}** - *{person['position']}* @ {person['company']}")
                st.markdown(f"🔗 LinkedIn: {person.get('url', 'Unknown')}")
                st.markdown(f"📈 Similarity Score: `{person['similarity']}%` | Hybrid Score: `{person['hybrid_score']}`")
                st.markdown("---")

            with st.expander("ℹ️ What do the scores mean?"):
                st.markdown("""
                - **Similarity Score**: Measures how semantically close the person’s profile is to your query, using OpenAI embeddings (scaled 0–100).
                - **Hybrid Score**: Combines similarity score with connection proximity. Closer degrees (1° > 2° > 3°) get more weight.
                """)
    else:
        st.error("Please enter both your name and your query.")