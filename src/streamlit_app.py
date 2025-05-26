import streamlit as st
from utils.graphrag import graph_rag_query, parse_query_with_groq
import pandas as pd

# 🎨 Custom CSS for styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(90deg, rgba(126,147,198,1) 7%, rgba(127,196,194,1) 90%) !important;
        color: #1B1725;
    }
    .stApp {
        background: linear-gradient(90deg, rgba(126,147,198,1) 7%, rgba(127,196,194,1) 90%) !important;
        color: #1B1725;
    }
    .stTextInput>div>div>input {
        background-color: #D0BCDB;
        color: #1B1725;
        font-weight: 600;
        border: 1px solid #534B62;
    }
    .stButton>button {
        background-color: white !important;
        color: #1B1725 !important;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    .custom-box {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    .custom-box:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .score-box {
        background-color: rgba(255, 255, 255, 0.3);
        padding: 0.3rem 0.7rem;
        margin-left: 0.5rem;
        margin-right: 0.5rem;
        border-radius: 8px;
        display: inline-block;
        font-weight: bold;
        color: #1B1725;
    }
    .stDownloadButton > button {
        background-color: white !important;
        color: #1B1725 !important;  /* Raisin Black */
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s ease-in-out;
    }
    .stDownloadButton > button:hover {
        background-color: #e6e6e6 !important;
        color: #1B1725 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ✨ App title
st.markdown("### 🔗 <span style='color:#1B1725'>LinkedIn Network Search with</span> <span style='color:#534B62'><strong>GraphRAG</strong></span>", unsafe_allow_html=True)

# 🧑‍💼 User inputs
your_name = st.text_input("👤 Enter your name:")
user_query = st.text_input("🔍 Enter your query (e.g., 'Find Data Scientists' or 'Who works at ZS Associates'):")

# 🚀 Search action
if st.button("Search Network"):
    if your_name and user_query:
        results = graph_rag_query(your_name, user_query)

        # if results:
        #     st.markdown("### 📢 <span style='color:#1B1725'>Top Matches in Your Network</span>", unsafe_allow_html=True)
        #     for person in results:
        #         similarity_score = f"<span class='score-box'>{person['similarity']}%</span>" if 'similarity' in person else ""
        #         hybrid_score = f"🎯 Hybrid Score: <span class='score-box'>{person['hybrid_score']}</span>" if 'hybrid_score' in person else ""

        #         st.markdown(f"""
        #             <div class='custom-box'>
        #                 <p>👤 <strong>{person['name']}</strong><br>
        #                 <em>{person['position']} @ {person['company']}</em><br>
        #                 📊 Similarity Score: {similarity_score} {hybrid_score}
        #                 </p>
        #             </div>
        #         """, unsafe_allow_html=True)
        if results:
            st.markdown("### 📢 Top Matches in Your Network")
            for person in results:
                with st.container():
                    st.markdown(f"""
                        <div class='custom-box'>
                            <p>👤 <strong>{person['name']}</strong><br>
                            <em>{person['position']} @ {person['company']}</em><br>
                            📊 Similarity Score: <span class="score-box">{person['similarity']}%</span> 🎯 Hybrid Score: <span class="score-box">{person.get('hybrid_score', 'NA')}</span>
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

            # 🔽 Add CSV Download Option
            df = pd.DataFrame(results)
            csv = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download CSV of Matching People",
                data=csv,
                file_name='matched_connections.csv',
                mime='text/csv'
            )

            with st.expander("🔍 What do these scores mean?"):
                st.markdown("""
                ### 🧠 Similarity Score  
                - Measures how **semantically close** a person's profile is to your query using **LLM embeddings**.
                - It uses OpenAI’s embedding model to convert both the query and each profile (name, title, company) into numerical vectors.
                - These vectors are then compared using **cosine similarity**, scaled from 0 to 100%.
                - A higher score means the person's profile closely aligns with your search intent.

                ### 🕸️ Hybrid Score  
                - Combines the **semantic similarity** with the **proximity in your LinkedIn network**.
                - **Formula**: `Hybrid Score = 0.7 * Similarity Score + 0.3 * (30 - degree)`
                - Here, `degree` refers to how many hops away they are from you (1°, 2°, or 3° connection).
                - This score favors **relevant people who are closer to you**, making recommendations both meaningful and actionable.
                """)
        else:
            st.warning("⚠️ No matches found in your network for that query.")
    else:
        st.error("Please enter both your name and query to continue.")