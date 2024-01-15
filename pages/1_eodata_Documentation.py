import os
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt


st.set_page_config(page_title="/eodata documentation", page_icon="📈")
st.markdown("# /eodata documentation")
st.sidebar.header(" /eodata documentation")
st.write(
    """Data Availability after the official [Cloudferro Documentation for WEkEO](https://wekeo.docs.cloudferro.com/en/latest/eodata/EODATA-Collections-from-Copernicus-programme-on-WEkEO-Elasticity.html). """
)


#set working dir
#os.chdir('C:\\Users\\erdmann\\OneDrive - eumetsat.int\\Visual Studio\\eodata_dashboard')


#data import
ds = pd.read_csv('./data/cf_eodata_documentation.csv')

#data maipulation

todayminusyear = dt.datetime.now()-timedelta(days=365)
todayminusmonth = dt.datetime.now()-timedelta(days=30)

ds['end_date'] = pd.to_datetime(ds['end_date'], errors='ignore')

ds.loc[ds['start_date'] == 'today - 1 year', 'start_date'] = todayminusyear
ds.loc[ds['start_date'] == 'today - 1 month', 'start_date'] = todayminusmonth

#ds.loc[ds['start_date'] == 'today - 1 year', 'start_date']
ds['start_date'] = pd.to_datetime(ds['start_date'], errors='ignore')

ds['availability_duration'] = ds['end_date'] - ds['start_date']
ds = ds.sort_values(by='start_date')


# Sidebar with interactive options
select_satellite = st.sidebar.multiselect('Select Satellite', ds['Satellite'].unique(), default="Sentinel-3")
select_instrument = st.sidebar.multiselect('Select Instrument', ds[(ds['Satellite'].isin(select_satellite))]['Sensor'].unique(), default=['OLCI', 'SRAL', 'SLSTR'])
select_timeliness = st.sidebar.multiselect('Select timeliness', ds['timeliness'].unique(), default = ['NRT', 'STC', 'NTC'])
select_level = st.sidebar.multiselect('Select Processing level', ds['level'].unique(), default = [1, 2])

filtered_ds = ds[(ds['Satellite'].isin(select_satellite)) & (ds['Sensor'].isin(select_instrument)) & (ds['timeliness'].isin(select_timeliness)) & (ds['level'].isin(select_level))]

fig, ax = plt.subplots(figsize=(10, 6))

for index, row in filtered_ds.iterrows():
    # Plotting horizontal bars for each product
    ax.barh(row['Product type'], row['availability_duration'].days, left=row['start_date'], label=row['Product type'])

# Beautify the plot
ax.set_xlabel('Time')
ax.set_ylabel('Products')
ax.set_title('Timely Availability of Products')
#ax.legend()

# Display the plot in tab 1 using Streamlit

st.pyplot(fig)


display_ds = filtered_ds[['Satellite', 'Product type', 'Temporal Range']].set_index(['Satellite', 'Product type'])
st.write("Data Availability according to CF Documentation", display_ds.sort_index())