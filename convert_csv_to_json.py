import pandas as pd

df = pd.read_csv('data/nasa_cognition.csv')
df.to_json('data/nasa_cognition.json', orient='records', lines=True)
print("CSV converted to JSON.")

