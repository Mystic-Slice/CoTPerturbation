import streamlit as st
import json
import os
from pathlib import Path

import re
def extract_answer(s):
    ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")
    match = ANS_RE.search(s)
    if match:
        match_str = match.group(1).strip()
        match_str = match_str.replace(",", "")
        return match_str
    else:
        # check if the last part of the string is a number
        match_str = s.split()[-1].strip()
        if re.match(r'(\-?[0-9\.\,]+)', match_str):
            return match_str
    return 'invalid'

# --- Page Configuration ---
st.set_page_config(
    page_title="LLM Robustness Analyzer",
    page_icon="📊",
    layout="wide"
)

# --- CSS Styling for better readability ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .stMarkdown h3 {
        color: #31333F;
    }
    .comparison-header {
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
        text-align: center;
        padding: 5px;
        border-radius: 5px;
    }
    .header-clean { background-color: #d1fae5; color: #065f46; }
    .header-perturbed { background-color: #fee2e2; color: #991b1b; }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data
def load_summary(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def load_detail_file(base_path, llm_name, type_name, file_id):
    # Construct path: results/{llm_name}/{type}/{id}.json
    # We strip whitespace just in case
    path = Path(base_path) / llm_name.strip() / type_name.strip() / f"{file_id}.json"
    
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

# --- Sidebar Controls ---
st.sidebar.title("⚙️ Configuration")

# 1. File Selection
summary_file = st.sidebar.text_input("Summary JSON Path", value="results/accuracy_summary.json")
results_dir = st.sidebar.text_input("Results Directory Path", value="results")

# Load Data
data = load_summary(summary_file)

if not data:
    st.error(f"Could not find the summary file at `{summary_file}`. Please check the path in the sidebar.")
    st.stop()

# 2. Select LLM
llm_names = list(data.keys())
selected_llm = st.sidebar.selectbox("Select LLM Model", llm_names)

# 3. Select Type (e.g., ExtraSteps, MathError)
if selected_llm:
    types = list(data[selected_llm].keys())
    selected_type = st.sidebar.selectbox("Select Perturbation Type", types)
else:
    selected_type = None

st.sidebar.markdown("---")
st.sidebar.info("Use the dropdowns above to navigate through different models and perturbation types.")

# --- Main Content ---

if selected_llm and selected_type:
    st.title(f"Analysis: {selected_llm}")
    st.caption(f"Perturbation Type: **{selected_type}**")
    
    metrics = data[selected_llm][selected_type]

    # --- Section 1: High Level Metrics ---
    st.header("1. Performance Overview")
    
    # Row 1: Accuracy Stats
    c1, c2 = st.columns(2)
    c1.metric("Clean Accuracy", f"{metrics.get('clean_accuracy', 0):.2%}")
    c2.metric("Perturbed Accuracy", f"{metrics.get('perturbed_accuracy', 0):.2%}")
    
    # Row 2: Confusion Matrix Counts
    st.subheader("Transition Counts")
    cm1, cm2, cm3, cm4 = st.columns(4)
    
    with cm1:
        st.markdown('<div class="metric-card">✅ Clean Correct<br>✅ Perturbed Correct<br><h2>{}</h2></div>'.format(metrics.get("clean_corr_perturbed_corr", 0)), unsafe_allow_html=True)
    with cm2:
        st.markdown('<div class="metric-card">✅ Clean Correct<br>❌ Perturbed Incorrect<br><h2>{}</h2></div>'.format(metrics.get("clean_corr_perturbed_incorr", 0)), unsafe_allow_html=True)
    with cm3:
        st.markdown('<div class="metric-card">❌ Clean Incorrect<br>✅ Perturbed Correct<br><h2>{}</h2></div>'.format(metrics.get("clean_incorr_perturbed_corr", 0)), unsafe_allow_html=True)
    with cm4:
        st.markdown('<div class="metric-card">❌ Clean Incorrect<br>❌ Perturbed Incorrect<br><h2>{}</h2></div>'.format(metrics.get("clean_incorr_perturbed_incorr", 0)), unsafe_allow_html=True)

    st.markdown("---")

    # --- Section 2: Deep Dive into IDs ---
    st.header("2. Detailed Instance Inspector")
    
    # Define categories based on the JSON keys ending in _ids
    id_categories = {
        "✅ Clean Correct → ✅ Perturbed Correct": "clean_corr_perturbed_corr_ids",
        "✅ Clean Correct → ❌ Perturbed Incorrect (Regressions)": "clean_corr_perturbed_incorr_ids",
        "❌ Clean Incorrect → ✅ Perturbed Correct (Improvements)": "clean_incorr_perturbed_corr_ids",
        "❌ Clean Incorrect → ❌ Perturbed Incorrect": "clean_incorr_perturbed_incorr_ids",
    }
    
    selected_cat_label = st.selectbox("Select Category to Inspect", list(id_categories.keys()))
    json_key = id_categories[selected_cat_label]
    available_ids = metrics.get(json_key, [])
    
    st.write(f"**Found {len(available_ids)} instances in this category.**")
    
    if len(available_ids) > 0:
        # Selector for specific ID
        selected_id = st.selectbox("Select File ID", available_ids)
        
        # Load the specific details
        detail_data = load_detail_file(results_dir, selected_llm, selected_type, selected_id)
        
        if detail_data:
            # --- Displaying the Details ---
            
            # 1. The Core Question
            with st.expander("📝 Problem Statement & Gold Solution", expanded=True):
                st.markdown("**Question:**")
                st.info(detail_data.get('question', 'N/A'))
                
                col_gold_1, col_gold_2 = st.columns(2)
                with col_gold_1:
                    st.markdown("**Gold Solution:**")
                    st.code(detail_data.get('solution', 'N/A'), language='latex')
                with col_gold_2:
                    st.markdown("**Correct Answer:**")
                    st.success(extract_answer(detail_data.get('solution', 'N/A')))

            # 2. Side-by-Side Comparison
            st.markdown("### ⚔️ Clean vs. Perturbed Comparison")
            
            col_clean, col_perturbed = st.columns(2)
            
            # --- Left Column: Clean ---
            with col_clean:
                st.markdown('<div class="comparison-header header-clean">Clean Input</div>', unsafe_allow_html=True)

                st.markdown("**Clean Partial Solution:**")
                # Using text_area for scrollable large text or standard markdown
                clean_partial_sol = detail_data.get('clean_solution', 'N/A')
                st.markdown(f"```\n{clean_partial_sol}\n```")
                
                st.markdown("**Clean Solution:**")
                # Using text_area for scrollable large text or standard markdown
                clean_sol = detail_data.get('completed_solution_clean', 'N/A')
                st.markdown(f"```\n{clean_sol}\n```")
                
                st.markdown("**Extracted Answer:**")
                st.code(detail_data.get('answer_solution_clean', 'N/A'))

            # --- Right Column: Perturbed ---
            with col_perturbed:
                st.markdown('<div class="comparison-header header-perturbed">Perturbed Input</div>', unsafe_allow_html=True)

                st.markdown("**Perturbed Partial Solution:**")
                pert_partial_sol = detail_data.get('perturbed_solution', 'N/A')
                st.markdown(f"```\n{pert_partial_sol}\n```")
                
                st.markdown("**Perturbed Solution:**")
                pert_sol = detail_data.get('completed_solution_perturbed', 'N/A')
                st.markdown(f"```\n{pert_sol}\n```")
                
                st.markdown("**Extracted Answer:**")
                st.code(detail_data.get('answer_solution_perturbed', 'N/A'))
            
            # 3. Raw JSON Viewer (Optional, good for debugging)
            with st.expander("🔍 View Raw JSON Content"):
                st.json(detail_data)
                
        else:
            st.warning(f"Could not find detail file at: `results/{selected_llm}/{selected_type}/{selected_id}.json`")
    else:
        st.info("No IDs found for this specific category.")