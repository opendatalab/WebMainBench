'''
This script reads table data from a JSONL file and displays/edits it in a Streamlit app.
Example command:
    streamlit run /home/zhangshuo/Desktop/vscodeworkspace/WebMainBench/tools/label_tool.py -- WebMainBench/data/WebMainBench_test_0814_llm-webkit_filtered_table_results.jsonl
Note: there must be a space after --, otherwise it will raise an error. The data file path follows after.

'''

import json
import os
import streamlit as st
import markdown

import sys

# Support passing data file path via command-line argument
if len(sys.argv) > 1:
    DATA_FILE = sys.argv[1]
else:
    st.error("Please pass the data file path via command-line argument, e.g.: python read_table.py /path/to/data.jsonl")
    st.stop()

# Load all data
@st.cache_data(show_spinner=False)
def load_data():
    data = []
    if not os.path.exists(DATA_FILE):
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

# Update a single item only, avoiding full file rewrite
def update_single_item(index, new_item):
    lines = []
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if 0 <= index < len(lines):
        # Ensure only the corresponding line is replaced
        lines[index] = json.dumps(new_item, ensure_ascii=False) + "\n"
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

# Streamlit page layout
st.set_page_config(layout="wide")
st.title("WebMainBench Table Editor")

data = load_data()
if not data:
    st.warning("Data file not found or is empty.")
    st.stop()

# Select the entry to edit
index = st.sidebar.number_input("Select entry index", min_value=0, max_value=len(data)-1, value=0, step=1)
item = data[index]

# Three-column layout
col1, col2, col3 = st.columns([1.5, 1.5, 2])

with col1:
    st.subheader("HTML Render")
    # Try to use st.components.v1.html for enhanced HTML+CSS rendering
    try:
        st.components.v1.html(
            f'<div style="border:1px solid #ddd;padding:8px;overflow:auto;max-height:600px">{item.get("html","")}</div>',
            height=620,
            scrolling=True,
        )
    except Exception as e:
        st.markdown(
            f'<div style="border:1px solid #ddd;padding:8px;overflow:auto;max-height:600px">{item.get("html","")}</div>',
            unsafe_allow_html=True
        )
        st.info("st.components.v1.html is unavailable, falling back to st.markdown.")

with col2:
    st.subheader("Markdown Render")
    # Render Markdown in real time, prioritizing the content in the edit area
    # Use session_state to persist edited content
    if f"markdown_edit_{index}" not in st.session_state:
        st.session_state[f"markdown_edit_{index}"] = item.get("groundtruth_content", "")
    current_markdown = st.session_state[f"markdown_edit_{index}"]
    st.markdown(
        current_markdown,
        unsafe_allow_html=True
    )

with col3:
    st.subheader("Markdown Source (Editable)")
    # Update session_state in real time
    new_markdown = st.text_area(
        "Edit Markdown",
        value=st.session_state.get(f"markdown_edit_{index}", item.get("groundtruth_content", "")),
        height=600,
        key=f"markdown_edit_{index}"
    )
    # Submit button is only used to save to file
    if st.button("Submit Changes", key=f"submit_{index}"):
        if new_markdown != item.get("groundtruth_content", ""):
            # Only update the current entry to avoid full file rewrite and data overwrite
            data[index]["groundtruth_content"] = new_markdown
            update_single_item(index, data[index])
            load_data.clear()  # Clear cache to ensure fresh data is read next time
            st.success("Changes saved!")
        else:
            st.info("Content unchanged, no save needed.")
