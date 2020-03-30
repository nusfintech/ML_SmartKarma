# -*- coding: utf-8 -*-

# Commented out IPython magic to ensure Python compatibility.
# %pip install pandas_datareader --upgrade

from datetime import datetime, date
from pandas_datareader import data
import matplotlib.pyplot as plt
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')
import numpy as np
from pylab import rcParams
rcParams['figure.figsize'] = 10, 2
from statsmodels.tsa.arima_model import ARIMA
import math

spxTicker = '^SPX'
start_date = date(1990, 1, 1)
end_date = date.today()

panel_data = data.DataReader('^SPX', 'stooq',start_date,end_date)

panel_data

close_SPY = pd.DataFrame(index=panel_data.index, data=panel_data['Close'])

close_SPY.head()

close = close_SPY['Close']

short_rolling_close = close.rolling(window=20).mean()
long_rolling_close = close.rolling(window=100).mean()

fig, ax = plt.subplots(figsize=(16,9))

ax.plot(close.index, close, label='S&P500')
ax.plot(short_rolling_close.index, short_rolling_close, label='20 days rolling')
ax.plot(long_rolling_close.index, long_rolling_close, label='100 days rolling')

ax.set_xlabel('Date')
ax.set_ylabel('Adjusted closing price ($)')
ax.legend()



df_log = np.log(close)
def arima_model(p,d,q):
  train_data, test_data = df_log[:int(len(df_log)*0.85)], df_log[int(len(df_log)*0.85):]
  model = ARIMA(df_log, order=(p, d, q))
  fitted = model.fit(disp=-1)
  fc, se, conf = fitted.forecast(len(test_data), alpha=0.05)
  future_index = pd.date_range(start = date.today(),periods= len(test_data))
  fc_series = pd.Series(fc, index=future_index)
  lower_series = pd.Series(conf[:, 0], index=future_index)
  upper_series = pd.Series(conf[:, 1], index=future_index)
  # Plot
  plt.figure(figsize=(16,9), dpi=72)
  plt.plot(np.exp(df_log), label='training')
  plt.plot(np.exp(fc_series), color = 'orange',label='Future Predicted Stock Price')
  plt.fill_between(lower_series.index, np.exp(lower_series), np.exp(upper_series), 
                      color='k', alpha=.10)
  plt.title('S & P 500 Index Price Prediction')
  plt.xlabel('Time')
  plt.ylabel('Price')
  plt.legend(loc='upper left', fontsize=8)
  plt.legend(loc='upper left', fontsize=8)

arima_model(3,2,1)
