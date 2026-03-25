from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval
import time

def main():
    # Initialize tvDatafeed
    # For better access, provide your TradingView username and password
    # tv = TvDatafeed('your_username', 'your_password')
    tv = TvDatafeed()

    print("--- Historical Data Example ---")

    # 1. Fetching Stock Index Futures Data (NIFTY)
    # fut_contract=1 fetches the current continuous futures contract (NIFTY1!)
    print("\nFetching NIFTY Current Month Continuous Futures (1-hour interval)...")
    nifty_futures_data = tv.get_hist(
        symbol='NIFTY',
        exchange='NFO',
        interval=Interval.in_1_hour,
        n_bars=10,
        fut_contract=1
    )
    if nifty_futures_data is not None:
        print(nifty_futures_data.tail())
    else:
        print("Failed to fetch futures data.")

    # 2. Fetching Stock Index Options Data
    # First, we need to find the correct ticker for an option
    print("\nSearching for BANKNIFTY Call Options...")
    # Search for a specific strike and type
    search_results = tv.search_symbol('BANKNIFTY 45000 CE', 'NFO')

    if search_results:
        # Get the ticker from the first result
        option_ticker = search_results[0]['symbol']
        print(f"Found option ticker: {option_ticker}")

        print(f"Fetching data for {option_ticker} (5-minute interval)...")
        option_data = tv.get_hist(
            symbol=option_ticker,
            exchange='NFO',
            interval=Interval.in_5_minute,
            n_bars=10
        )
        if option_data is not None:
            print(option_data.tail())
        else:
            print("Failed to fetch options data.")
    else:
        print("No option found for the search query.")

    print("\n--- Live Data Feed Example ---")

    # Define a callback function for live data
    def live_callback(seis, data):
        print(f"\n[LIVE UPDATE] {seis.symbol} ({seis.interval.name}):")
        print(data)

    # Initialize live datafeed
    tv_live = TvDatafeedLive()

    try:
        # Monitor NIFTY Index (Spot) and NIFTY Futures (Continuous)
        print("Starting live feed for NIFTY Index and Futures...")

        # Spot Index
        nifty_spot_seis = tv_live.new_seis('NIFTY', 'NSE', Interval.in_1_minute)
        tv_live.new_consumer(nifty_spot_seis, live_callback)

        # We can also add others
        # banknifty_seis = tv_live.new_seis('BANKNIFTY', 'NSE', Interval.in_1_minute)
        # tv_live.new_consumer(banknifty_seis, live_callback)

        print("Listening for updates for 30 seconds... (Press Ctrl+C to stop)")
        time.sleep(30)

    except KeyboardInterrupt:
        print("Stopping live feed...")
    finally:
        tv_live.del_tvdatafeed()

if __name__ == "__main__":
    main()
