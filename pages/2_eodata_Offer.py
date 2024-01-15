import os 
import pandas as pd
import datetime as dt
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from matplotlib.lines import Line2D

st.set_page_config(page_title="/eodata offer", page_icon="📈")
st.markdown("# /eodata offer")
st.sidebar.header(" /eodata offer")
st.write( """This dashboard shows the data types available for Sentinel-3 in the /eodata folder.""")


# Checkbox to toggle visibility
show_df = st.checkbox("Show Data")


    


#set working dir
#os.chdir('C:\\Users\\erdmann\\OneDrive - eumetsat.int\\Visual Studio\\eodata_dashboard')


#data import data offer dataframe
ds = pd.read_csv('./data/eodatabase.csv')
ds = ds.dropna( axis=0, how='all')
#data maipulation
today = dt.date.today
ds['end_date'] = pd.to_datetime(ds['end_date'], errors='ignore')
ds['start_date'] = pd.to_datetime(ds['start_date'], errors='ignore')
ds['availability_duration'] = ds['end_date'] - ds['start_date']
ds = ds.sort_values(by='start_date')

ds['baseline_collection'] = ds['baseline_collection'].astype('str')
#ds['level'] = ds['level'].astype('int').astype('str')
ds['Product type'] = ds['sensor']+' Level-'+ds['level'].astype('int').astype('str')+' '+ds['timeliness']

ds['specs'] = ds['status']+' '+ds['processor']+' '+ds['baseline_collection']

ds['product'] = ds['eodata_folder'].str.rstrip('_')

#data import data documentation dataframe

ds_doc = pd.read_csv('./data/cf_eodata_documentation.csv')

#data maipulation

todayminusyear = dt.datetime.now()-timedelta(days=365)
todayminusmonth = dt.datetime.now()-timedelta(days=30)

ds_doc['end_date'] = pd.to_datetime(ds_doc['end_date'], errors='ignore')

ds_doc.loc[ds_doc['start_date'] == 'today - 1 year', 'start_date'] = todayminusyear
ds_doc.loc[ds_doc['start_date'] == 'today - 1 month', 'start_date'] = todayminusmonth
ds_doc['start_date'] = pd.to_datetime(ds_doc['start_date'], errors='ignore')
ds_doc['availability_duration'] = ds_doc['end_date'] - ds_doc['start_date']
#ds_doc['level'] = ds_doc['level'].astype('int').astype('str')
#ds_doc
# Sidebar with interactive options
select_instrument = st.sidebar.multiselect('Select Instrument', ds['sensor'].unique(), default = 'OLCI')
select_timeliness = st.sidebar.multiselect('Select timeliness', ds[(ds['sensor'].isin(select_instrument))]['timeliness'].unique(), default = ['NRT', 'NTC'])
select_level = st.sidebar.multiselect('Select Processing level', ds[(ds['sensor'].isin(select_instrument)) & (ds['timeliness'].isin(select_timeliness))]['level'].unique(), default = [0,1,2])
select_product = st.sidebar.multiselect('Select Product Type', np.sort(ds[(ds['sensor'].isin(select_instrument)) & (ds['timeliness'].isin(select_timeliness)) & (ds['level'].isin(select_level))]['product'].unique()), default=['OL_0_EFR', 'OL_1_EFR', 'OL_2_WFR'])
mode = st.sidebar.selectbox('Select Mode', ['Aggregate', 'Details'])
enable_comparison = st.sidebar.checkbox('Compare with the Documentation', value=False)

filtered_df1 = ds[(ds['sensor'].isin(select_instrument)) & (ds['timeliness'].isin(select_timeliness)) & (ds['level'].isin(select_level))& (ds['product'].isin(select_product))].sort_values(['eodata_folder', 'start_date'], ascending = [True, False])

grouped_df1 =filtered_df1.groupby(['eodata_folder', 'Product type', 'timeliness', 'product']).agg({
    'start_date': 'min',
    'end_date': 'max'
}).reset_index().sort_values(['eodata_folder'], ascending = True)


# Text widget that is conditionally displayed
if show_df:
    st.dataframe(grouped_df1)

filtered_df2 = ds_doc[(ds_doc['Sensor'].isin(select_instrument)) & (ds_doc['timeliness'].isin(select_timeliness)) & (ds_doc['level'].isin(select_level))].sort_values(['Product type'], ascending = True)


# Plotting the time ranges from both DataFrames
# Plotting the time ranges
fig, ax = plt.subplots(figsize=(10,8))

bar_width = 0.25  # Width of each bar

bar_positions = np.arange(len(grouped_df1))

# Define color mapping for timeliness
timeliness_color_map = {'NRT': 'blue', 'NTC': 'green', 'STC': 'red'}
timeliness_labels = {'NRT': 'Near Real Time', 'NTC': 'Non-Time Critical', 'STC': 'Short-Time Critical'}


if mode == "Aggregate":
    # Plotting bars for complete time range
    color = grouped_df1['timeliness'].map(timeliness_color_map.get)
    ax.barh(bar_positions, 
            (grouped_df1['end_date'] - grouped_df1['start_date']).dt.days,
            height=bar_width, 
            left=grouped_df1['start_date'],
            color=color,
            alpha=0.6)
    
    


if mode == "Details":

    # Plotting bars for complete time range
    
    
    # Plotting bars for complete time range
    color = grouped_df1['timeliness'].map(timeliness_color_map.get)
    ax.barh(bar_positions, 
            (grouped_df1['end_date'] - grouped_df1['start_date']).dt.days,
            height=bar_width, 
            left=grouped_df1['start_date'],
            color=color,
            alpha=0.6)
    # Plotting bars for each spec within each eodata_folder
    for i, (product_type, timeliness, product) in enumerate(grouped_df1[['eodata_folder', 'timeliness', 'product']].itertuples(index=False)):
        folder_data = filtered_df1[filtered_df1['timeliness'] == timeliness]
        product_data = folder_data[filtered_df1['product'] == product]
        product_type_data = product_data[product_data['eodata_folder'] == product_type]
        unique_specs = product_type_data['specs'].unique()

        for j, spec in enumerate(unique_specs):
            spec_data = product_type_data[product_type_data['specs'] == spec]
            # Convert start_date and end_date to the number of days since a reference date
            start_date_numeric = (spec_data['start_date'] - pd.Timestamp("1970-01-01")).dt.days.values
            end_date_numeric = (spec_data['end_date'] - pd.Timestamp("1970-01-01")).dt.days.values
            ax.barh(bar_positions[i] - (j+2) * bar_width*0.5,
                    end_date_numeric - start_date_numeric,
                    height=bar_width*0.3, left=start_date_numeric,
                    alpha=0.6, color = "grey")
        # Add label for each bar
            for index, value in enumerate(spec_data['specs'].unique()):
                ax.text((start_date_numeric[index] + end_date_numeric[index]) / 2,
                        bar_positions[i] - (j+2) * bar_width*0.5,
                        value, ha='center', va='center', color='black')

if enable_comparison: 
    # Plotting bars for documentation above the complete time range bar
    for i, product_type in enumerate(grouped_df1['Product type']):
        documentation_data = filtered_df2[filtered_df2['Product type'] == product_type]
        start_date_numeric = documentation_data['start_date'].values.astype('datetime64[D]').astype(float)
        end_date_numeric = documentation_data['end_date'].values.astype('datetime64[D]').astype(float)
        ax.barh(bar_positions[i],
                end_date_numeric - start_date_numeric,
                height=bar_width*0.9, left=start_date_numeric,
                label=f'{product_type} - Documentation', alpha=0.6, color='orange')
    


legend_items = [Line2D([0], [0], color=timeliness_color_map[timeliness], label=timeliness_labels[timeliness]) for timeliness in timeliness_labels]
ax.legend(handles=legend_items)

# Beautify the plot
ax.set_yticks(bar_positions)
ax.set_yticklabels(grouped_df1['eodata_folder'].tolist())
ax.set_xlabel('Time')
ax.set_ylabel('eodata_folders')
ax.set_title('eodata_folder Time Range with Specs')
#ax.legend()
# Display the plot in Streamlit
st.pyplot(fig)

if enable_comparison:
    st.markdown ('Documented time frames for the selected Product types are displayed in the table below and as yellow bars inside the graph')
    filtered_df2

st.markdown("""### Customization Options:""")
st.write ('''**Select Instrument**: Select Instrument to display''')
st.write ('''**Select Timeliness**: Select Timeliness (NRT, NTC, STC) to display''')
st.write ('''**Select Processing Level**: Select Processing Level (0: Level-0 Products, 1: Level-1 Products, 2: Level-2 Products)''')
st.write ('''**Select Product Type**: Select Product Type to Display. Product Type is made up of instrument index (e.g. OL), Level and product identifyier (WFR: water Full Resolution)''')
st.write ('''**Select Mode**: Select level of Detail for Visualization. 
- *Aggregated* shows the availability any data in the selected product type and timeliness. 
- *Details* show the detailes specifications of Processor, Original/Reprocessed, Baseline Collection''')

st.sidebar.markdown('''<hr>''', unsafe_allow_html=True)
st.sidebar.markdown('''<small>[eodata dashboard v1](https://github.com/annaerdmann/eodata_dashboard)  | Jan 2024 | [Anna-Lena Erdmann]</small>''', unsafe_allow_html=True)