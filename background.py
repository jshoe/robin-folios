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
import requests

def pprint(field):
    # Pretty print JSON fields
    print(json.dumps(field, sort_keys=True, indent=4, separators=(',', ': ')))

def sort_by(df, field):
    # Sort DataFrame by header name
    print(df.sort_values(field, 0, False).round(2).to_string(index=False))

my_trader = Robinhood()
logged_in = my_trader.login(username="YOUR USERNAME", password="YOUR PASSWORD")

def make_buy_order(symbol, quantity=1, bid_price=None):
    instrument = my_trader.instruments(symbol)[0]
    my_trader.place_buy_order(instrument, quantity, bid_price)

def make_sell_order(symbol, quantity=1, bid_price=None):
    instrument = my_trader.instruments(symbol)[0]
    my_trader.place_sell_order(instrument, quantity, bid_price)

def get_pre_market_gainers():
    # Only for the CNN page here
    base = 'http://money.cnn.com/data/premarket/'
    try:
        response = urllib.request.urlopen(base)
        data = response.read()
    except urllib.error.HTTPError:
        return []

    # Get list of gainer symbols
    reg_ex = 'symb=(.+?)\"'
    text = data.decode('utf-8')
    gainers = re.findall(reg_ex, text, re.M)[:5]

    # Get list of gainer prices
    reg_ex = '\"wsod_aRight\">(\d+\.\d+)\<'
    prices = re.findall(reg_ex, text, re.M)[:5]

    # Filter gainer list by cutoff price
    results = []
    n = 0
    for stock in gainers:
        if float(prices[n]) < 100: # Cutoff price
            results.append(stock)
        n += 1
    return results

def get_pre_market_gainers_2():
    # Only for the stockmarketwatch page here
    print("Loading page")
    base = "http://www.thestockmarketwatch.com/markets/pre-market/today.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    try:
        response = requests.get(base, headers=headers)
        text = response.content.decode()
    except urllib.error.HTTPError:
        print("Error loading page")
        return []

    # Get list of gainer symbols
    reg_ex = 'symbol\" href=\"/stock/\?stock=(.+?)\"'
    gainers = re.findall(reg_ex, text, re.M)[:15]

    # Get list of gainer prices
    reg_ex = 'div class=\"lastPrice\"\>([0-9].+?)\<'
    prices = re.findall(reg_ex, text, re.M)[:15]

    # Get list of gainer volumes
    reg_ex = 'class=\"volume2\">([0-9].*?)\<'
    volumes = re.findall(reg_ex, text, re.M)[:15]

    # Filter gainer list by cutoff price and volume
    results = []
    n = 0
    for stock in gainers:
        if float(prices[n]) < 100: # Cutoff price
            if float(volumes[n]) > 150: # At least this volume
                results.append(stock)
        n += 1
        
    #pdb.set_trace()
    return results

to_be_sold = []

def buy_pre_market_gainers():
    global to_be_sold
    print(str(datetime.datetime.now()) + ": buy_pre_market_gainers called")
    gainers = get_pre_market_gainers_2()
    for stock in gainers:
        print("Buying " + stock)
        make_buy_order(stock, 1, 100)
        to_be_sold.append(stock)
        time.sleep(2)

def sell_scheduled():
    # Sell stocks scheduled to be sold
    global to_be_sold
    print(str(datetime.datetime.now()) + ": sell_scheduled called")
    for stock in to_be_sold:
        print("Selling " + stock)
        make_sell_order(stock, 1, 0.5)
        time.sleep(2)
    to_be_sold = []

def action():
    print(datetime.datetime.now())
    print("Action running now")
    buy_pre_market_gainers()

def schedule_actions():
    # Example:     nohup python MyScheduledProgram.py &> ~/Desktop/output.log
    # ps auxw to see running ones
    print(datetime.datetime.now())
    print("Starting to run")
    times = ['6:07', '06:24']

    # Buy today's positions
    for set_time in times:
        schedule.every().monday.at(set_time).do(action)
        schedule.every().tuesday.at(set_time).do(action)
        schedule.every().wednesday.at(set_time).do(action)
        schedule.every().thursday.at(set_time).do(action)
        schedule.every().friday.at(set_time).do(action)

    # Sell yesterday's positions
    set_time = '06:01'
    schedule.every().monday.at(set_time).do(sell_scheduled)
    schedule.every().tuesday.at(set_time).do(sell_scheduled)
    schedule.every().wednesday.at(set_time).do(sell_scheduled)
    schedule.every().thursday.at(set_time).do(sell_scheduled)
    schedule.every().friday.at(set_time).do(sell_scheduled)

    while True:
        schedule.run_pending()
        sys.stdout.flush()
        time.sleep(1) # Check every 1 second

schedule_actions()
