
import streamlit as st
import pandas as pd
import plotly.express as px
from scripts.train_model import CourseRecommender

# --- CONFIGURATION ---
st.set_page_config(
    page_title="CourseAI",
    page_icon="🎓",
    layout="wide"
)

# Load Engine
@st.cache_resource
def load_engine():
    # Ensure we point to the correct file
    return CourseRecommender(data_path='data/final_courses.csv')

try:
    rec = load_engine()
    df = rec.df
except Exception as e:
    st.error(f"Error loading engine: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 CourseAI")
    st.markdown("---")
    selected_source = st.multiselect(
        "Platform", 
        options=df['source_domain'].unique(), 
        default=df['source_domain'].unique()
    )
    filtered_df = df[df['source_domain'].isin(selected_source)]
    st.metric("Total Courses", len(filtered_df))

# --- MAIN CONTENT ---
tab_dash, tab_search, tab_data = st.tabs(["🚀 Dashboard", "🔍 Smart Search", "💾 Dataset"])

with tab_dash:
    st.header("App Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Courses", len(filtered_df))
    col2.metric("Avg Rating", f"{filtered_df['rating'].mean():.2f}")
    col3.metric("Avg Duration", f"{filtered_df['duration_hours'].mean():.0f}h")
    col4.metric("Top Category", filtered_df['category'].mode()[0] if not filtered_df.empty else "N/A")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Category Distribution")
        if not filtered_df.empty:
            cat_counts = filtered_df['category'].value_counts().head(10)
            st.bar_chart(cat_counts)
    with c2:
        st.subheader("Rating Distribution")
        if not filtered_df.empty:
            fig = px.histogram(filtered_df, x="rating", nbins=10)
            st.plotly_chart(fig, use_container_width=True)

with tab_search:
    st.header("Search Courses")
    query = st.text_input("What do you want to learn?", placeholder="e.g. Python, Marketing...")
    
    if query:
        results = rec.search(query, top_k=6)
        if not results:
            st.warning("No matches found.")
        else:
            for r in results:
                # Standard Streamlit Expander instead of custom Card
                with st.expander(f"{r['title']} ({int(r['similarity_score']*100)}% Match)"):
                    st.write(f"**Platform:** {r['source_domain'].title()}")
                    st.write(f"**Instructor:** {r['partner']}")
                    st.write(f"**Rating:** {r['rating']} ({r['num_ratings']} reviews)")
                    st.write(f"**Duration:** {r['duration_hours']} hours")
                    
                    desc = r.get('full_description', '')
                    if desc:
                        st.caption(f"{str(desc)[:300]}...")
                        
                    st.markdown(f"[**View Course**]({r['link']})")

with tab_data:
    st.dataframe(filtered_df, use_container_width=True)
