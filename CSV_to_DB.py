import datetime
import io
import sqlite3 as sl

import pandas as pd
# from matplotlib import pyplot as plt
# from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.neural_network import MLPClassifier
# from sklearn.pipeline import make_pipeline
# from sklearn.preprocessing import StandardScaler

pd.set_option('display.max_columns', None)

# Create/Connect database
conn = sl.connect('minimum_wage.db')
curs = conn.cursor()

# Create our table if it doesn't already exist
# Manually specify table name, column names, and columns types
curs.execute('DROP TABLE IF EXISTS minimum_wage')
curs.execute('CREATE TABLE IF NOT EXISTS '
             'minimum_wage (`Year` integer, `State` text, `Minimum_Wage` real)')
conn.commit()  # don't forget to commit changes before continuing

# Use pandas to read the CSV to df
# Select just the columns you want using optional use columns param
df = pd.read_csv('minimum_wage.csv', usecols=['Year', 'State', 'State.Minimum.Wage'], encoding='utf-8')
# drop nulls just like pandas hw
df = df[df["State.Minimum.Wage"].notnull()]
print('First 3 df results:')
print(df.head(3))

table_name = 'minimum_wage'

df.to_sql(name=table_name, con=conn, if_exists='replace', index=False)

