##-- Download file from S3 to local
s3_client.download_file(f'{S3_BUCKET}', 'population_data.json', 'population_data_localfile.json')

##-- Load JSON file and flatten
read_json = read_file('population_data_localfile.json')
json_obj = json.loads(read_json)
flattened_data = json_obj['data']
data_types_p2 = {'id':'str', 'nation':'str', 'slug_nation':'str', 'id_year':'int','year':'int', 'population':'int'}
col_mapping_p2 = {'ID Nation':'id', 'Nation':'nation', 'Slug Nation':'slug_nation','ID Year':'id_year', 'Year':'year', 'Population':'population'}
df_p2 = pd.DataFrame(flattened_data)
df_p2.rename(columns=col_mapping_p2, inplace=True)
df_p2 = df_p2.astype(data_types_p2)

##-- Filter DataFrame: 2013-2018
filtered_df = df_p2[df_p2['year'].isin([year for year in range(2013, 2019)])]
# filtered_df.head()

##-- Calculate mean & standard deviation
mean_pop = filtered_df['population'].mean()
std_pop = filtered_df['population'].std()

#print(f"\nMean Population: {mean_pop:.2f}")
#print(f"\nStandard Deviation: {std_pop:.2f}")

##-- Download file from S3 to local
s3_client.download_file(f'{S3_BUCKET}', 'pr.data.0.Current', 'current_localfile.txt')

##-- Load CSV file 
data_types_p1 = {'series_id':'str', 'year':'int', 'period':'str', 'value':'float', 'footnote_codes':'str'}
df_p1 = pd.read_csv('current_localfile.txt', sep="\t", dtype=data_types_p1)
df_p1.rename(columns=lambda x: x.strip(), inplace=True)
df_p1 = df_p1.map(lambda x: x.replace(' ', '') if isinstance(x, str) else x)
# df_p1.head()

##-- Group by 'series_id', sum the 'value' and find the max
grouped_df = df_p1.groupby('series_id')['value'].sum().reset_index()
max_value_row = grouped_df[grouped_df['value'] == grouped_df['value'].max()]
# grouped_df.head()

##-- filter dataframe 1
filtered_df_p1 = df_p1[(df_p1['series_id'] == 'PRS30006032') & (df_p1['period'] == 'Q01')]
# filtered_df_p1.head()

##-- filter dataframe 2
filtered_df_p2 = df_p2[ df_p2['year'].isin(filtered_df_p1['year']) ]
# filtered_df_p2.head()

##-- Merge dataframes 1 & 2
result = pd.merge(filtered_df_p1, filtered_df_p2, left_on='year', right_on='year', how='left')
report_df = result[['series_id', 'year', 'value', 'population']]
# display(report_df)