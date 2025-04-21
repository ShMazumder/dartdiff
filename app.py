# app.py

import streamlit as st
import zipfile
import tempfile
from package_diff_checker import compare_directories
import pandas as pd

st.set_page_config(page_title="Package Diff Checker", layout="wide")

st.title("📦 Package Difference Checker")

col1, col2 = st.columns(2)
with col1:
    old_zip = st.file_uploader("Upload Old Version (ZIP)", type="zip")
with col2:
    new_zip = st.file_uploader("Upload New Version (ZIP)", type="zip")

if old_zip and new_zip:
    with tempfile.TemporaryDirectory() as old_dir, tempfile.TemporaryDirectory() as new_dir:
        with zipfile.ZipFile(old_zip, 'r') as zip_ref:
            zip_ref.extractall(old_dir)
        with zipfile.ZipFile(new_zip, 'r') as zip_ref:
            zip_ref.extractall(new_dir)

        with st.spinner("🔍 Comparing packages..."):
            compare_directories(old_dir, new_dir, output_csv="diff_report.csv")
            df = pd.read_csv("diff_report.csv")

        st.success("✅ Comparison complete!")
        st.dataframe(df)

        st.download_button("📥 Download CSV", df.to_csv(index=False), "diff_report.csv", "text/csv")

