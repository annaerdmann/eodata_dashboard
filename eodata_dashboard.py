# import packages

import streamlit as st



# Build the app with Streamlit

st.set_page_config(
    page_title="Overview",
    page_icon="👋",
)

st.write("""
# /eodata 
#### Analysis of Cloudferros object storage earth observation data archive /eodata
\n
\n
Contents of the Dashboard: 

1. Exploration tool for /eodata Documentation

2. Sentinel 3 data in /eodata

""")
st.sidebar.markdown('''<hr>''', unsafe_allow_html=True)
st.sidebar.markdown('''<small>[GitHub](https://github.com/annaerdmann/eodata_dashboard)  | Jan 2024 | Anna-Lena Erdmann</small>''', unsafe_allow_html=True)