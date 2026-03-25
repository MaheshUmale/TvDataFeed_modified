# tvDatafeed

`tvDatafeed` is a Python library for fetching historical and live data from TradingView using a websocket connection. It allows you to access data for a wide range of symbols across different exchanges, including stocks, indices, futures, and options.

## Features

- **Historical Data**: Fetch historical OHLCV data for any symbol on TradingView.
- **Live Data**: Subscribe to real-time data updates for multiple symbols and intervals.
- **Search**: Search for symbols and exchanges directly.
- **Support for Futures & Options**: Specialized support for continuous futures contracts and specific option tickers.
- **Multi-Exchange**: Access data from NSE, NFO, MCX, NASDAQ, NYSE, BINANCE, and more.

## Installation

You can install the dependencies using pip:

```bash
pip install pandas websocket-client requests rookiepy python-dateutil
```

## Quick Start

### Basic Initialization

```python
from tvDatafeed import TvDatafeed, Interval

# Initialize without login (limited data)
tv = TvDatafeed()

# Or initialize with login for more data access
# username = 'YourTradingViewUserName'
# password = 'YourTradingViewPassword'
# tv = TvDatafeed(username, password)
```

### Fetching Historical Data

```python
# Fetch 100 bars of NIFTY daily data from NSE
nifty_data = tv.get_hist(symbol='NIFTY', exchange='NSE', interval=Interval.in_daily, n_bars=100)
print(nifty_data)
```

## Stock Index Options and Futures

`tvDatafeed` provides powerful ways to access derivatives data.

### 1. Stock Index Futures
For Indian markets (NSE/NFO), use `exchange='NFO'`. For continuous futures contracts, use the `fut_contract` parameter.

- `fut_contract=1`: Current Month Continuous Contract (e.g., `NIFTY1!`)
- `fut_contract=2`: Next Month Continuous Contract (e.g., `NIFTY2!`)

```python
# Fetch NIFTY Current Month Continuous Futures
nifty_fut = tv.get_hist(symbol='NIFTY', exchange='NFO', interval=Interval.in_1_hour, n_bars=100, fut_contract=1)
```

### 2. Stock Index Options
To fetch data for a specific option, you need the exact ticker. You can find it using the `search_symbol` method.

```python
# Search for NIFTY 19000 Call Option
results = tv.search_symbol('NIFTY 19000 CE', 'NFO')
# Typically results will be like NIFTY2390719000CE
if results:
    ticker = results[0]['symbol']
    option_data = tv.get_hist(symbol=ticker, exchange='NFO', interval=Interval.in_5_minute, n_bars=50)
```

## Live Data Consumption

`TvDatafeedLive` allows you to monitor multiple symbols simultaneously using a consumer-callback pattern.

```python
from tvDatafeed import TvDatafeedLive, Interval

def my_callback(seis, data):
    print(f"New bar for {seis.symbol}:")
    print(data)

tv_live = TvDatafeedLive()

# Simple one-line subscription
tv_live.subscribe('NIFTY', 'NSE', Interval.in_1_minute, my_callback)

# Alternatively, manual steps for more control:
# 1. Create a 'Seis' (Symbol-Exchange-Interval Set)
# nifty_seis = tv_live.new_seis('NIFTY', 'NSE', Interval.in_1_minute)
# 2. Register a consumer with the callback
# tv_live.new_consumer(nifty_seis, my_callback)

# The live feed runs in a separate thread. 
# Keep the main thread alive.
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    tv_live.del_tvdatafeed()
```

## Intervals
Available intervals include:
- `Interval.in_1_minute`
- `Interval.in_3_minute`
- `Interval.in_5_minute`
- `Interval.in_15_minute`
- `Interval.in_30_minute`
- `Interval.in_45_minute`
- `Interval.in_1_hour`
- `Interval.in_2_hour`
- `Interval.in_3_hour`
- `Interval.in_4_hour`
- `Interval.in_daily`
- `Interval.in_weekly`
- `Interval.in_monthly`

## Disclaimer
This library is intended for educational purposes and personal use. Ensure you comply with TradingView's Terms of Service.
