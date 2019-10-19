# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.2.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import pandas as pd
import numpy as np
import os
from matplotlib import pyplot as plt
from datetime import datetime

# +
base_path = os.path.normpath(r'..\unparsed-data')
excel_file = 'S&P500Data.xlsx'
excel_path = os.path.join(base_path, excel_file)
missing_values = ['#N/A N/A']
xlsx = pd.ExcelFile(excel_path)
stock_sheets = list()
for i in range(len(xlsx.sheet_names)):
    sheet = xlsx.sheet_names[i]
    temp = xlsx.parse(sheet, header=None, skiprows=5 if i > 0 else None, \
                    skip_footer=1, na_values=missing_values)
    if i > 1:
        temp['Ticker'] = stock_sheets[0][0][i-2][:-10]
        temp = temp[:-1]
        temp = temp.dropna()
        temp.columns = ['Dates', 'Close', 'Volume', 'Open', 'High', 'Low', 'Ticker']
        temp['Direction'] = temp.Close.sub(temp.Close.shift(), fill_value=0)
        temp['Direction'] = pd.Series(np.where(temp.Direction.values > 0, 1, 0),
          temp.index)
        temp = temp[1:]
    stock_sheets.append(temp)

stocks = pd.concat(stock_sheets[2:])
stocks.columns = ['Dates', 'Close', 'Volume', 'Open', 'High',\
                  'Low', 'Ticker', 'Direction']
# -

stocks.head()

stocks.isnull().sum()

type(stocks['Dates'].values[0])

# +
#usable_stocks = ['TSLA', 'GOOG', 'JNJ', 'JPM', 'V', 'AAPL','AMZN', 'MSFT', 'FB', 'BRK/B', 'BRK B', 'BRK.B']
#stocks = stocks[stocks['Ticker'].isin(usable_stocks)]
#stocks['Ticker'].unique().tolist()
# -

pathtocsv=os.path.normpath(r'..\cleaned\stocksusable.csv')
stocks.to_csv(pathtocsv, index=False)


