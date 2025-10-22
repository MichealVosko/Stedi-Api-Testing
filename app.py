import streamlit as st
from ui.realtime_eligibility import render_form
from ui.batch_eligibility import render_batch_form
from ui.render_batch_results import render_batch_results
from ui.batch_realtime import render_batch_realtime


st.set_page_config(page_title="Eligibility Checker", layout="centered")

st.title("Eligibility Checker")

tabs = st.tabs(["Check Real-Time Eligibility", "Batch Eligibility Check", "View Batch Results", "Batch Realtime Check"])

with tabs[0]:
    render_form()

with tabs[1]:
    render_batch_form()

with tabs[2]:
    render_batch_results()

with tabs[3]:
    render_batch_realtime()