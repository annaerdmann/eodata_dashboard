import os 
import pandas as pd
import datetime as dt
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from matplotlib.lines import Line2D

st.set_page_config(page_title="Recommendation", page_icon="📈")
st.markdown("# Comparison of the /eodata offer against the EUM recommendation")
st.sidebar.header(" recommended data use")
st.write( """This dashboard compares the eodata offer against the EUMETSAT data offer and recommendation""")


# Checkbox to toggle visibility
show_df = st.checkbox("Show Data")


# Custom function to format integers with leading zeros
def format_with_zeros(value):
    return f"{value:03d}"


# import the EUM data available

ds_eum = pd.read_csv('./data/eum_s3_data.csv')
ds_eum = ds_eum.dropna( axis=0, how='all')

#data maipulation
today = dt.date.today
todayminusyear = dt.datetime.now()-timedelta(days=365)
todayminusmonth = dt.datetime.now()-timedelta(days=30)
ds_eum.loc[ds_eum['end_date'] == 'today - 1 year', 'end_date'] = todayminusyear
ds_eum.loc[ds_eum['end_date'] == 'today - 1 month', 'end_date'] = todayminusmonth
ds_eum['end_date'] = pd.to_datetime(ds_eum['end_date'], errors='ignore')
ds_eum['start_date'] = pd.to_datetime(ds_eum['start_date'], errors='ignore')
ds_eum['availability_duration'] = ds_eum['end_date'] - ds_eum['start_date']
ds_eum = ds_eum.sort_values(by='start_date')
ds_eum['baseline_collection'] = ds_eum['baseline_collection'].apply(format_with_zeros)
ds_eum['processing'] =np.where(ds_eum['status'] == 'Original', ds_eum['timeliness'] , ds_eum['status'])
custom_order = ['Reprocessed', 'NTC', 'STC', 'NRT']
ds_eum['processing'] = pd.Categorical(ds_eum['processing'], categories=custom_order, ordered=True)


ds_eum_group =ds_eum.groupby(['product', 'processing', 'baseline_collection']).agg({
    'start_date': 'min',
    'end_date': 'max'
}).reset_index().sort_values(['product'], ascending = True)

# create dataframe with EUM recommendation

# Sort the DataFrame based on conditions
best_products_df_sort = ds_eum[['product', 'processing', 'baseline_collection', 'start_date', 'end_date']].sort_values(
                            by=['product', 'processing', 'baseline_collection'], ascending=[False, True, False])

#print (best_products_df_sort)

#best_products_df_sort = best_products_df_sort[best_products_df_sort['product'] == 'OL_1_EFR']
#print(best_products_df_sort)
# Initialize the adjusted DataFrame
eum_recomm_data = pd.DataFrame(columns=['product', 'start_date_eum', 'end_date_eum', 'processing', 'baseline_collection'])
start_date = best_products_df_sort['start_date'].min()
end_date = best_products_df_sort['end_date'].max()
for product in best_products_df_sort['product'].unique():
    best_products_df = best_products_df_sort[best_products_df_sort['product'] == product].reset_index()
    adjusted_df = pd.DataFrame(columns=['product', 'start_date', 'end_date', 'processing', 'baseline_collection'])
    current_date = start_date
    while current_date <= end_date:
        for index, row in best_products_df.iterrows():
            #print (index)
            start_date_row = row['start_date']
            end_date_row = row['end_date']
            if start_date_row == current_date:
                if (best_products_df.head(index)['start_date'].min()>start_date_row )& (best_products_df.head(index)['start_date'].min()<end_date_row):#start date of smaller index > end date row: end date = start_date of smaller index
                    end_date_product = (best_products_df.head(index)['start_date'].min())-pd.Timedelta(days=1)
                    #current_date = end_date_product
                else: 
                    end_date_product = end_date_row #end date==end_date row
                    #current_date = end_date_product-pd.Timedelta(days=1)
                adjusted_df = pd.concat([adjusted_df, pd.DataFrame([{'product': row['product'], 'start_date': current_date, 'end_date': end_date_product, 'processing': row['processing'], 'baseline_collection': row['baseline_collection']}])], ignore_index=True)
                current_date = end_date_product
                break
            if (current_date > start_date_row)&(current_date < end_date_row):
                if (best_products_df.head(index)['start_date'].min()>start_date_row )& (best_products_df.head(index)['start_date'].min()<end_date_row):#start date of smaller index > end date row: end date = start_date of smaller index
                    end_date_product = (best_products_df.head(index)['start_date'].min())-pd.Timedelta(days=1)
                    #current_date = end_date_product
                else: 
                    end_date_product = end_date_row #end date==end_date row
                    #current_date = end_date_product-pd.Timedelta(days=1)
                adjusted_df = pd.concat([adjusted_df, pd.DataFrame([{'product': row['product'], 'start_date': current_date, 'end_date': end_date_product, 'processing': row['processing'], 'baseline_collection': row['baseline_collection']}])], ignore_index=True)
                current_date = end_date_product
                break
                
                # if len(adjusted_df) > 1:
                #     adjusted_df['end_date'].loc[len(adjusted_df)-2] = current_date
                # last_product = row['product']
            

        # Move to the next day
        current_date += pd.Timedelta(days=1)
    eum_recomm_data = pd.concat([eum_recomm_data, adjusted_df])
    eum_recomm_data['duration_eum'] = (eum_recomm_data['end_date'] - eum_recomm_data['start_date']).dt.days
    eum_recomm_data= eum_recomm_data[['product', 'processing', 'baseline_collection', 'duration_eum', 'start_date', 'end_date']]
    #print (eum_recomm_data)

# join EUM recommendation with all EUM data

full_eum_recomm_eum = pd.merge(ds_eum, eum_recomm_data, on=['product', 'processing', 'baseline_collection'], how='outer')
#full_eum_recomm_eum['start_date_eum'] = full_eum_recomm_eum['start_date_y'].fillna(today)
#full_eum_recomm_eum['start_date_eum'] = pd.to_datetime(full_eum_recomm_eum['start_date_y'].fillna(today), errors='ignore')
#full_eum_recomm_eum['start_date_y'] = full_eum_recomm_eum['start_date_y'].fillna(timedelta(days=0))
#full_eum_recomm_eum['end_date_y'] = full_eum_recomm_eum['end_date_y'].fillna(timedelta(days=0))

#full_eum_recomm_eum

#create eodata offer in same formatted data frame

#data import data offer dataframe
ds = pd.read_csv('./data/eodatabase.csv')
ds = ds.dropna( axis=0, how='all')
#data maipulation
today = dt.date.today
ds['end_date_eodata'] = pd.to_datetime(ds['end_date'], errors='ignore')
ds['start_date_eodata'] = pd.to_datetime(ds['start_date'], errors='ignore')
ds['availability_duration'] = ds['end_date_eodata'] - ds['start_date_eodata']
ds = ds.sort_values(by='start_date_eodata')
ds['baseline_collection'] = ds['baseline_collection'].apply(format_with_zeros)
ds['processing'] =np.where(ds['status'] == 'Original', ds['timeliness'] , ds['status'])
ds['product'] = ds['eodata_folder'].str.rstrip('_')
#ds['duration_eodata']= (ds['end_date_eodata'] - ds['start_date_eodata']).dt.days
ds= ds[['start_date_eodata', 'end_date_eodata', 'processor', 'processing', 'baseline_collection', 'product']]
ds = ds.groupby(['processing', 'baseline_collection', 'product',]).agg({
    'start_date_eodata': 'min',
    'end_date_eodata': 'max'
}).reset_index().sort_values(['product'], ascending = True)
ds['duration_eodata']= (ds['end_date_eodata'] - ds['start_date_eodata']).dt.days


eum_recomm_eodata = pd.merge(full_eum_recomm_eum, ds, on=['product', 'processing', 'baseline_collection'], how='outer')
eum_recomm_eodata['processing'] = pd.Categorical(eum_recomm_eodata['processing'], categories=custom_order, ordered=True)
#eum_recomm_eodata

# Sidebar with interactive options
select_instrument = st.sidebar.multiselect('Select Instrument', ds_eum['sensor'].unique(), default = 'OLCI')
select_product = st.sidebar.multiselect('Select Product Type', np.sort(ds_eum[(ds_eum['sensor'].isin(select_instrument))]['product'].unique()))#, default=['OL_0_EFR', 'OL_1_EFR', 'OL_2_WFR'])

eum_recomm = st.sidebar.checkbox('Show EUMETSAT Recommendation', value=False)
eodata_offer = st.sidebar.checkbox('Show /eodata offer', value=False)


filtered_ds = eum_recomm_eodata[(eum_recomm_eodata['sensor'].isin(select_instrument)) & (eum_recomm_eodata['product'].isin(select_product))].sort_values(['product', 'processing', 'baseline_collection', 'start_date_x'], ascending = [True,False,True, False])

# Text widget that is conditionally displayed
if show_df:
    st.dataframe(filtered_ds)


# Plotting the time ranges
#fig, ax = plt.subplots(figsize=(10,8))

bar_width = 0.25  # Width of each bar


# Define color mapping for timeliness
timeliness_color_map = {'NRT': 'blue', 'NTC': 'green', 'STC': 'red', 'Reprocessed': 'yellow'}
timeliness_labels = {'NRT': 'Near Real Time', 'NTC': 'Non-Time Critical', 'STC': 'Short-Time Critical', 'Reprocessed': 'Reprocessed'}

unique_products = filtered_ds['product'].unique()
if len(unique_products) > 1: 

    # Create subplots for each product
    fig, axs = plt.subplots(len(unique_products), 1, figsize=(8, 4 * len(unique_products)), sharex=True)

    # Iterate over unique products
    for i, product in enumerate(unique_products):
        product_data = filtered_ds[filtered_ds['product'] == product]
        #product_data
        bar_positions = np.arange(len(product_data))
        # Plotting bars for each product
        color = product_data['processing'].map(timeliness_color_map)
        axs[i].barh(bar_positions, 
            (product_data['end_date_x'] - product_data['start_date_x']).dt.days,
            height=bar_width, 
            left=product_data['start_date_x'],
            color=color,
            alpha=0.6)
        
        if eum_recomm:
            axs[i].barh(bar_positions, 
            product_data['duration_eum'],
            height=bar_width*1.3, 
            left=product_data['start_date_y'],
            edgecolor='red',
            facecolor='none',
            alpha=0.9)
        if eodata_offer:
            axs[i].barh(bar_positions, 
            product_data['duration_eodata'],
            height=bar_width*1.1, 
            left=product_data['start_date_eodata'],
            edgecolor='blue',
            facecolor='none',
            alpha=0.9)
        
        # Customize subplot
        axs[i].set_yticks(bar_positions)
        axs[i].set_yticklabels(product_data['processing'].astype('str')+' '+product_data['baseline_collection'].tolist())
        axs[i].set_xlabel('Time')
        axs[i].set_ylabel(product)
        
    # Adjust layout
    plt.tight_layout()
    st.pyplot(fig)

if len(unique_products)==1: 
    # Create subplots for each product
    fig, axs = plt.subplots(1, 1, figsize=(8, 4 ))

    # Iterate over unique products
    
    product_data = filtered_ds
    #product_data
    bar_positions = np.arange(len(product_data))
    # Plotting bars for each product
    color = product_data['processing'].map(timeliness_color_map)
    axs.barh(bar_positions, 
        (product_data['end_date_x'] - product_data['start_date_x']).dt.days,
        height=bar_width, 
        left=product_data['start_date_x'],
        color=color,
        alpha=0.6)

    if eum_recomm:
            axs.barh(bar_positions, 
            product_data['duration_eum'],
            height=bar_width*1.3, 
            left=product_data['start_date_y'],
            edgecolor='red',
            facecolor='none',
            alpha=0.9)
    if eodata_offer:
            axs.barh(bar_positions, 
            product_data['duration_eodata'],
            height=bar_width*1.1, 
            left=product_data['start_date_eodata'],
            edgecolor='blue',
            facecolor='none',
            alpha=0.9)    
        # Customize subplot
    axs.set_yticklabels(product_data['processing'].astype('str')+' '+product_data['baseline_collection'].tolist())
    axs.set_yticks(bar_positions)
    axs.set_xlabel('Time')
    axs.set_ylabel(unique_products[0])
        
    # Adjust layout
    plt.tight_layout()
    st.pyplot(fig)

# Plotting bars for complete time range
# color = filtered_ds['timeliness'].map(timeliness_color_map.get)
# ax.barh(bar_positions, 
#         (filtered_ds['end_date'] - filtered_ds['start_date']).dt.days,
#         height=bar_width, 
#         left=filtered_ds['start_date'],
#         color=color,
#         alpha=0.6)



# # Beautify the plot
# ax.set_yticks(bar_positions)
# ax.set_yticklabels(filtered_ds['product'].tolist())
# ax.set_xlabel('Time')
# ax.set_ylabel('product')
# ax.set_title('eodata_folder Time Range with Specs')
#ax.legend()
# Display the plot in Streamlit



# #data import data offer dataframe
# ds = pd.read_csv('./data/eodatabase.csv')
# ds = ds.dropna( axis=0, how='all')
# #data maipulation
# today = dt.date.today
# ds['end_date'] = pd.to_datetime(ds['end_date'], errors='ignore')
# ds['start_date'] = pd.to_datetime(ds['start_date'], errors='ignore')
# ds['availability_duration'] = ds['end_date'] - ds['start_date']
# ds = ds.sort_values(by='start_date')
# ds['baseline_collection'] = ds['baseline_collection'].apply(format_with_zeros)
# ds['product'] = ds['eodata_folder'].str.rstrip('_')