import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


DATA_FREQ = '1min'
MIN = 1
HOUR = 60*MIN
DAY = 24*HOUR

RETURN_TIMEFRAME = 3*HOUR

def diff(x):
    return (x.iloc[-1] - x.iloc[0])/x.iloc[0]

df_processed = []

list_of_stocks = [f"AAPL_2020-03-24_2022-02-12_{DATA_FREQ}"] #

from xgboost import XGBRegressor
factors = ['Short_std', 'Lng_std', 'H/O', 'L/O', 'C/O', '%15Min_wav', '%Hour_wav', '%Day_wav', '%5Day_wav', '%Short_std', '%Lng_std']
model = XGBRegressor()
model.load_model("model_sklearn.json")

for stock in list_of_stocks:
    df = pd.read_csv("data/" + stock + ".csv", parse_dates=[0])

    # BASIC DATA
    df['TP'] = (df['open'] + df['low'] + df['high'])/3 # Calculate Typical Price
    df['Short_std'] = df['TP'].rolling(30*MIN).std()
    df['Lng_std'] = df['TP'].ewm(alpha = 0.00015).std()

    df['15Min_wav'] = df['TP'].ewm(alpha = 0.1).mean()
    df['Hour_wav'] = df['TP'].ewm(alpha = 0.03).mean()
    df['Day_wav'] = df['TP'].ewm(alpha = 0.0015).mean()
    df['5Day_wav'] = df['TP'].ewm(alpha = 0.0003).mean()
    
    # CHANGES IN BASIC DATA
    df['H/O'] = df['high']/df['open']
    df['L/O'] = df['low']/df['open']
    df['C/O'] = df['close']/df['open']

    df['%15Min_wav'] = df['15Min_wav'].rolling(15*MIN).apply(diff)
    df['%Hour_wav'] = df['Hour_wav'].rolling(HOUR).apply(diff)
    df['%Day_wav'] = df['Day_wav'].rolling(DAY).apply(diff)
    df['%5Day_wav'] = df['5Day_wav'].rolling(5*DAY).apply(diff)

    df['%Short_std'] = df['Short_std'].rolling(30*MIN).apply(diff)
    df['%Lng_std'] = df['Lng_std'].rolling(5*DAY).apply(diff)

    # INDEPENDENT VARIABLE
    df['return'] = df['Hour_wav'].rolling(RETURN_TIMEFRAME).apply(diff)
    df['return'] = df['return'].shift(-RETURN_TIMEFRAME)

    # ML buy/sell signal
    df['EV'] = model.predict(df[factors])

    ''' # standard moving averages
    df['15MIN'] = df['TP'].rolling(15*MIN).mean()
    df['HOUR'] = df['TP'].rolling(HOUR).mean()
    df['DAY'] = df['TP'].rolling(DAY).mean()
    df['5DAY'] = df['TP'].rolling(5*DAY).mean()

    df['%15MIN'] = df['15MIN'].rolling(15*MIN).apply(diff)
    df['%HOUR'] = df['HOUR'].rolling(HOUR).apply(diff)
    df['%DAY'] = df['DAY'].rolling(DAY).apply(diff)
    df['%5DAY'] = df['5DAY'].rolling(5*DAY).apply(diff)
     
    df['returnToDayClose'] = df['5DAY'].rolling(5*DAY).apply(diff)
    '''
    df.to_csv("data/" + stock + "_Processed.csv", index=False) # Save to CSV
    df_processed.append(stock + "_Processed")
    
print(df_processed)