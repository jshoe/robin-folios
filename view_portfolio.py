from Robinhood import Robinhood
import pdb
import json
import numpy as np
import pandas as pd
import urllib.request
import re
import schedule
import time
import sys
import datetime
from datetime import datetime, timedelta
import codecs

def pprint(field):
    # Pretty print JSON fields
    print(json.dumps(field, sort_keys=True, indent=4, separators=(',', ': ')))

def sort_by(df, field):
    # Sort DataFrame by header name
    print(df.sort_values(field, 0, False).round(2).to_string(index=False))

my_trader = Robinhood()
logged_in = my_trader.login(username="YOUR USERNAME", password="YOUR PASSWORD")

price_data = {}

def make_main_table():
    all_positions = my_trader.positions()['results']

    # Get data series
    securities = []
    average_buy_prices = []
    quantities = []
    cur_prices = []
    names = []
    ma_5 = [] # Moving average 5-day    
    ma_15 = [] # Moving average 15-day
    ma_30 = [] # Moving average 30-day
    ma_50 = [] # Moving average 50-day
    ma_100 = [] # Moving average 100-day

    # Debug
    #all_positions = all_positions[:10]

    for pos in all_positions:
        # Skip if not held
        if int(float(pos['quantity'])) == 0:
            continue

        # Iterate through all positions and extract data series
        data = my_trader.session.get(pos['instrument']).json()
        quote_info = my_trader.quote_data(data['symbol'])
        securities.append(data['symbol'])
        names.append(data['name'])

        average_buy_prices.append(float(pos['average_buy_price']))
        quantities.append(int(float(pos['quantity'])))

        cur_price = quote_info['last_trade_price']
        cur_prices.append(float(cur_price))

        # Fetch price data for each position
        fetch_price_data(data['symbol'])
        ma_5.append(fetch_moving_average(data['symbol'], 5))                
        ma_15.append(fetch_moving_average(data['symbol'], 15))
        ma_30.append(fetch_moving_average(data['symbol'], 30))
        ma_50.append(fetch_moving_average(data['symbol'], 50))
        ma_100.append(fetch_moving_average(data['symbol'], 100))

    # Make series
    s0 = pd.Series(names, name='Name')
    s1 = pd.Series(securities, name='Ticker')
    s2 = pd.Series(quantities, name='Quantity')
    s3 = pd.Series(average_buy_prices, name='AvgBuyPrice')
    s4 = pd.Series(cur_prices, name='CurPrice')

    # Construct data frame
    df = pd.concat([s1, s2, s3, s4], axis=1)
    df['BuyTotal'] = df['AvgBuyPrice'] * df['Quantity']
    df['CurTotal'] = df['CurPrice'] * df['Quantity']
    df['P/L ($)'] = df['CurTotal'] - df['BuyTotal']
    df['P/L (%)'] = (df['P/L ($)'] / df['BuyTotal']) * 100
    total_equity = my_trader.market_value()
    df['Weight (%)'] = df['CurTotal'] / total_equity * 100
    df['MA (5)'] = ma_5
    df['MA (15)'] = ma_15
    df['MA (30)'] = ma_30
    df['MA (50)'] = ma_50
    df['MA (100)'] = ma_100
    df.fillna(0)

    # Check conditions for all stocks
    df['MA Flags'] = check_conditions(df)
    
    # Set display settings
    def print_table():
        print(df.sort_values('P/L (%)', 0, False).round(2).to_string(index=False))

    def show_names():
        df.insert(0, 'Name', s0)
        print_table()

    def hide_names():
        del df['Name']
        print_table()

    pd.set_option('display.width', 3000)
    print_table()

    # Enter interactive debugger
    pdb.set_trace()
    return df

def print_help():
    print("Example:     sort_by(df, 'P/L ($)')")
    print("             show_names()")
    print("             hide_names()")
    print("MA (15) =    15-day simple moving average")

def fetch_price_data(stock):
    utf_decoder = codecs.getreader("utf-8")

    start_date = datetime.now() - timedelta(days=130)
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        stocks_base_URL = 'https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.historicaldata%20where%20symbol%20%3D%20'
        URL_end = '%20and%20startDate%20%3D%20%22' + start_date + '%22%20and%20endDate%20%3D%20%22' + end_date + '%22&format=json&diagnostics=true&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback='

        query = stocks_base_URL + "%22" + stock + "%22" + "%2C"
        query = query[:-3] + URL_end
        api_response = urllib.request.urlopen(query)

        response_data = json.load(utf_decoder(api_response))['query']['results']['quote']
        price_data[stock] = response_data        
    except:
        print("ERROR fetching price data")
        pdb.set_trace()

def fetch_moving_average(stock, num_days):
    # num_days = number of days to fetch
    try:
        data = price_data[stock][:num_days]
    except:
        return 0.0

    # Find the average
    total = 0.0
    for day in data:
        total += float(day["Close"])
    average = total / num_days
    return average

def check_conditions(df):
    flags = []
    for index, row in df.iterrows():
        flag = ''
        ma_to_test = ['MA (5)', 'MA (15)', 'MA (30)', 'MA (50)', 'MA (100)']
        for ma in ma_to_test:
            if row['CurPrice'] < row[ma]:
                flag += '↓'
            elif row['CurPrice'] > row[ma]:
                flag += '↑'
        if flag == '':
            flags.append('')
        else:
            flags.append(flag)
    return flags

print_help()
make_main_table()
print_help()
