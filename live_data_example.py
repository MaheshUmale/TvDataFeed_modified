from tvDatafeed import TvDatafeedLive, Interval
import time
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def main():
    # 1. Initialize TvDatafeedLive
    # You can provide username/password if you have a Pro account for faster/more data
    tv_live = TvDatafeedLive()

    # 2. Define a callback function
    # This function will be called whenever a new bar is completed
    def on_new_bar(seis, data):
        print(f"\n>>> LIVE UPDATE for {seis.symbol} ({seis.exchange}) at {seis.interval.name} interval:")
        print(data)
        # Here you can push this data to your trading bot, database, or UI
        # example: push_to_client(data.to_json())

    print("--- Starting Live Data Subscriptions ---")

    try:
        # 3. Use the new 'subscribe' method for a simple interface
        # Subscribing to NIFTY (NSE) at 1-minute interval
        print("Subscribing to NIFTY (NSE) 1-minute bars...")
        tv_live.subscribe(
            symbol='NIFTY',
            exchange='NSE',
            interval=Interval.in_1_minute,
            callback=on_new_bar
        )

        # Subscribing to Reliance (NSE) at 1-minute interval
        print("Subscribing to RELIANCE (NSE) 1-minute bars...")
        tv_live.subscribe(
            symbol='RELIANCE',
            exchange='NSE',
            interval=Interval.in_1_minute,
            callback=on_new_bar
        )

        # 4. Keep the main thread alive to receive updates
        print("\nListening for live updates... Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 5. Clean up and stop the live feed threads
        tv_live.del_tvdatafeed()
        print("Live datafeed stopped.")

if __name__ == "__main__":
    main()
