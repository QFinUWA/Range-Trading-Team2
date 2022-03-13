import pandas as pd
import time
import multiprocessing as mp

# local imports
from backtester import engine, tester
from backtester import API_Interface as api

training_period = 30 # 20 for demo
standard_deviations = 3.5

def logic(account, lookback): # Logic function to be used for each time interval in backtest 
    
    try:
        today = len(lookback)-1
        if(today > training_period):
            # If df['BUY'] is True, buy stock
            if(lookback['BUY'][today]):
                for position in account.positions:
                    account.close_position(position, 1, lookback['close'][today])
                if(account.buying_power > 0):
                    account.enter_position('long', account.buying_power, lookback['close'][today])
            # If df['SELL'] is True, sell stock
            if(lookback['SELL'][today]):
                for position in account.positions:
                    account.close_position(position, 1, lookback['close'][today])
                if(account.buying_power > 0):
                    account.enter_position('short', account.buying_power, lookback['close'][today])
    except Exception as e:
        print(e)
        pass  # Handles lookback errors in beginning of dataset

def preprocessData(list_of_stocks):
    list_of_stocks_processed = []
    for stock in list_of_stocks:
        df = pd.read_csv("data/" + stock + ".csv", parse_dates=[0])
        df['TP'] = (df['close'] + df['low'] + df['high'])/3 # Calculate Typical Price
        df['std'] = df['close'].rolling(training_period).std(ddof=0) # Calculate Standard Deviation
        df['MA-TP'] = df['TP'].rolling(training_period).mean() # Calculate Moving Average of Typical Price
        df['BOLU'] = df['MA-TP'] + standard_deviations*df['std'] # Calculate Upper Bollinger Band (3.5 for demo)
        df['BOLD'] = df['MA-TP'] - standard_deviations*df['std'] # Calculate Lower Bollinger Band (3.5 for demo)
        df["BUY"] = df['close'].gt(df['BOLU']) # Calculate if price is above upper band
        df["SELL"] = df['close'].lt(df['BOLD']) # Calculate if price is below lower band
        df.to_csv("data/" + stock + "_Processed.csv", index=False) # Save to CSV
        list_of_stocks_processed.append(stock + "_Processed")
    return list_of_stocks_processed

if __name__ == "__main__":
    list_of_stocks = ["TSLA_2020-03-01_2022-01-20_1min"] 
    # list_of_stocks = ["TSLA_2020-03-09_2022-01-28_15min"] # List of stock data csv's to be tested, located in "data/" folder 
    list_of_stocks_proccessed = preprocessData(list_of_stocks) # Preprocess the data
    starttime = time.time() # Start timer
    results = tester.testArr(list_of_stocks_proccessed, logic, chart=True) # Run backtest on list of stocks using the logic function

    print("training period" + str(training_period))
    print("standard deviations" + str(standard_deviations))
    print(results) # Print results
    df = pd.DataFrame(list(results),columns=["Buy and Hold","Strategy","Longs","Sells","Shorts","Covers","Stdev_Strategy","Stdev_Hold","Coin"]) # Create dataframe of results
    df.to_csv("resultsoftesting.csv",index =False) # Save results to csv
    # print('That took {} seconds'.format(time.time() - starttime)) # Print time taken to run backtest