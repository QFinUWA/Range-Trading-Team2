from turtle import pos
import pandas as pd
import time
import multiprocessing as mp

# local imports
from backtester import engine, tester
from backtester import API_Interface as api

training_period = 20 # How far the rolling average takes into calculation
standard_deviations = 3.5 # Number of Standard Deviations from the mean the Bollinger Bands sit

def GetPosition(account, close):
    invested = 0
    for position in account.positions: # Close all current positions
        sin = 1 if position.type_ == 'long' else -1
        invested += position.shares*close*sin

    return (invested/account.total_value(close))

def SetPosition(position, account, close):
    cur_pos = GetPosition(account, close)
    buy = account.total_value(close)*(position - cur_pos)

    for position in account.positions:
        # first if buying, try and remove shorts | if selling, try and remove longs
        if buy > 0 and position.type_ == 'short':
            value = position.shares*close
            account.close_position(position, min(1, buy/value), close)
            buy = min(0, buy - value)
        
        # first if selling, try and remove longs
        elif buy < 0 and position.type_ == 'long':
            value = position.shares*close
            
            account.close_position(position, min(1, -buy/value), close)
            buy = min(0, buy + value)

    # if still not at position, make trade
    if buy != 0 and account.buying_power>0:
        typ = 'long' if buy > 0 else 'short'

        account.enter_position(typ, min(abs(buy), account.buying_power), close)


def logic(account, lookback): # Logic function to be used for each time interval in backtest 
    
    today = len(lookback)-1
    if(today == 0):
        SetPosition(1,account, lookback['close'][today])
        print(GetPosition(account, lookback['close'][today]))
    if(today == 3000):
        SetPosition(-1,account, lookback['close'][today])
        print(GetPosition(account, lookback['close'][today]))
    if(today == 5000):
        SetPosition(0,account, lookback['close'][today])
        print(GetPosition(account, lookback['close'][today]))
    if(today == 10000):
        SetPosition(0.7,account, lookback['close'][today])
        print(GetPosition(account, lookback['close'][today]))
'''
preprocess_data() function:
    Context: Called once at the beginning of the backtest. TOTALLY OPTIONAL. 
             Each of these can be calculated at each time interval, however this is likely slower.

    Input:  list_of_stocks - a list of stock data csvs to be processed

    Output: list_of_stocks_processed - a list of processed stock data csvs
'''
def preprocess_data(list_of_stocks):
    list_of_stocks_processed = []
    for stock in list_of_stocks:
        df = pd.read_csv("data/" + stock + ".csv", parse_dates=[0])
        df['TP'] = (df['close'] + df['low'] + df['high'])/3 # Calculate Typical Price
        df['std'] = df['TP'].rolling(training_period).std() # Calculate Standard Deviation
        df['MA-TP'] = df['TP'].rolling(training_period).mean() # Calculate Moving Average of Typical Price
        df['BOLU'] = df['MA-TP'] + standard_deviations*df['std'] # Calculate Upper Bollinger Band
        df['BOLD'] = df['MA-TP'] - standard_deviations*df['std'] # Calculate Lower Bollinger Band
        df.to_csv("data/" + stock + "_Processed.csv", index=False) # Save to CSV
        list_of_stocks_processed.append(stock + "_Processed")
    return list_of_stocks_processed

if __name__ == "__main__":
    # list_of_stocks = ["TSLA_2020-03-01_2022-01-20_1min"] 
    list_of_stocks = ["TSLA_2020-03-09_2022-01-28_15min"]#, "AAPL_2020-03-24_2022-02-12_15min"] # List of stock data csv's to be tested, located in "data/" folder 
    list_of_stocks_proccessed = preprocess_data(list_of_stocks) # Preprocess the data
    results = tester.test_array(list_of_stocks_proccessed, logic, chart=True) # Run backtest on list of stocks using the logic function

    print("training period " + str(training_period))
    print("standard deviations " + str(standard_deviations))
    df = pd.DataFrame(list(results), columns=["Buy and Hold","Strategy","Longs","Sells","Shorts","Covers","Stdev_Strategy","Stdev_Hold","Stock"]) # Create dataframe of results
    df.to_csv("results/Test_Results.csv", index=False) # Save results to csv