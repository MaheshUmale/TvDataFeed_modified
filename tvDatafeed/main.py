import datetime
import enum
import json
import logging
import random
import re
import string
import pandas as pd
from websocket import create_connection
import requests
import json
import rookiepy 


logger = logging.getLogger(__name__)


class Interval(enum.Enum):
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"


class TvDatafeed:
    __sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    __search_url = 'https://symbol-search.tradingview.com/symbol_search/?text={}&hl=1&exchange={}&lang=en&type=&domain=production'
    __ws_headers = json.dumps({"Origin": "https://data.tradingview.com"})
    __signin_headers = {'Referer': 'https://www.tradingview.com'}
    __ws_timeout = 5

    def __init__(self, username=None, password=None, auto_login=True, chromedriver_path=None, cookies=None) -> None:
        
        try: 
            # 1. Get cookies from your browser
            if cookies is None:
                basecookies = rookiepy.brave(['https://www.tradingview.com','https://www.in.tradingview.com'])
                print(basecookies)
                cookies = rookiepy.to_cookiejar(basecookies)
                print(cookies)
        except Exception as e:
            print(f"Error obtaining cookies: {e}")
            import traceback
            traceback.print_exc()
            cookies = None

        self.ws_debug = False
        self.session = requests.Session()

        # 1. Load cookies into the session if provided
        if cookies:
            self.session.cookies.update(cookies)
            print(f"Cookies manually loaded into session. {cookies}")

        # 2. Pass session to auth to extract token from cookies or login
        self.token = self.__auth(username, password)

        print(f" TOKEN : {self.token}")
        if self.token is None:
            self.token = "unauthorized_user_token"

        self.ws = None
        # Note: self.session is overwritten by a string in the original library 
        # (which is a bug in the original code, but we will keep it for compatibility)
        self.ws = None
        self.session_id = self.__generate_session() 
        self.chart_session = self.__generate_chart_session()


    def __auth(self, username, password):
        # Check if we already have a sessionid cookie from rookiepy
        sessionid = self.session.cookies.get('sessionid', domain='.tradingview.com')
        print(" __AUTH -------------------")
        if (username is None or password is None):
            # If no credentials, try to fetch the token using existing session cookies
            print(f" sessionid = {sessionid}")
            if sessionid:
                try:
                    # Request the user config page to get the auth_token
                    response = self.session.get("https://www.tradingview.com")
                    print("------------------FINDING auth_token in page response -------------")
                    # If it returns plain text token or JSON, handle here:
                    # print(response.text)
                     # Use Regex to find the value after "auth_token":"
                    # This looks for the long JWT string inside the " " quotes
                    match = re.search(r'"auth_token":"([^"]+)"', response.text)
                    
                    if match:
                        token = match.group(1)
                        print(f"Successfully extracted token: {token[:10]}...")
                        return token
                    else:
                        logger.error("Could not find auth_token in the page HTML")
                        return None
                except Exception as e:
                    logger.error(f"Error during token extraction: {e}")
                    return None
            return None 

        else:
            # Standard login logic
            print("Standard LOGIN TRY ----------???")
            data = {"username": username, "password": password, "remember": "on"}
            try:
                response = self.session.post(
                    url=self.__sign_in_url, data=data, headers=self.__signin_headers)
                token = response.json()['user']['auth_token']
                return token
            except Exception as e:
                logger.error('error while signin')
                return None
    
    def __create_connection(self):
        logging.debug("creating websocket connection")
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket", headers=self.__ws_headers, timeout=self.__ws_timeout
        )

    @staticmethod
    def __filter_raw_message(text):
        try:
            found = re.search('"m":"(.+?)",', text).group(1)
            found2 = re.search('"p":(.+?"}"])}', text).group(1)

            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")

    @staticmethod
    def __generate_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters)
                                for i in range(stringLength))
        return "qs_" + random_string

    @staticmethod
    def __generate_chart_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters)
                                for i in range(stringLength))
        return "cs_" + random_string

    @staticmethod
    def __prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def __construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def __create_message(self, func, paramList):
        return self.__prepend_header(self.__construct_message(func, paramList))

    def __send_message(self, func, args):
        m = self.__create_message(func, args)
        if self.ws_debug:
            print(m)
        self.ws.send(m)

    @staticmethod
    def __create_df(raw_data, symbol):
        try:
            out = re.search('"s":\\[(.+?)\\}\\]', raw_data).group(1)
            x = out.split(',{"')
            data = list()
            volume_data = True

            for xi in x:
                xi = re.split("\\[|:|,|\\]", xi)
                ts = datetime.datetime.fromtimestamp(float(xi[4]))

                row = [ts]

                for i in range(5, 10):

                    # skip converting volume data if does not exists
                    if not volume_data and i == 9:
                        row.append(0.0)
                        continue
                    try:
                        row.append(float(xi[i]))

                    except ValueError:
                        volume_data = False
                        row.append(0.0)
                        logger.debug('no volume data')

                data.append(row)

            data = pd.DataFrame(
                data, columns=["datetime", "open",
                               "high", "low", "close", "volume"]
            ).set_index("datetime")
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error(f"no data, please check the exchange and symbol: {symbol}")

    @staticmethod
    def __format_symbol(symbol, exchange, contract: int = None):

        if ":" in symbol:
            pass
        elif contract is None:
            symbol = f"{exchange}:{symbol}"

        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"

        else:
            raise ValueError("not a valid contract")

        return symbol

    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        n_bars: int = 10,
        fut_contract: int = None,
        extended_session: bool = False,
    ) -> pd.DataFrame:
        """get historical data

        Args:
            symbol (str): symbol name
            exchange (str, optional): exchange, not required if symbol is in format EXCHANGE:SYMBOL. Defaults to None.
            interval (str, optional): chart interval. Defaults to 'D'.
            n_bars (int, optional): no of bars to download, max 5000. Defaults to 10.
            fut_contract (int, optional): None for cash, 1 for continuous current contract in front, 2 for continuous next contract in front . Defaults to None.
            extended_session (bool, optional): regular session if False, extended session if True, Defaults to False.

        Returns:
            pd.Dataframe: dataframe with sohlcv as columns
        """
        #TRIM spaces around symbol and convert to caps
        symbol = symbol.capitalize()
        symbol= symbol.strip()
        #if symbol contains :
        if ":" in symbol :
        # if symbol.startswith("NSE:") or symbol.startswith("BSE:") or symbol.startswith("MCX:") or symbol.startswith("NFO:") or symbol.ha:
            exchange = (symbol.split(":")[0]).strip()
            symbol = (symbol.split(":")[1]).strip()
        symbol = self.__format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )
        print(f"Formatted symbol: {symbol}")
        logger.info(f"Formatted symbol: {symbol}")
        interval = interval.value

        self.__create_connection()

        self.__send_message("set_auth_token", [self.token])
        self.__send_message("chart_create_session", [self.chart_session, ""])
        self.__send_message("quote_create_session", [self.session_id])
        self.__send_message(
            "quote_set_fields",
            [
                self.session_id,
                "ch",
                "chp",
                "current_session",
                "description",
                "local_description",
                "language",
                "exchange",
                "fractional",
                "is_tradable",
                "lp",
                "lp_time",
                "minmov",
                "minmove2",
                "original_name",
                "pricescale",
                "pro_name",
                "short_name",
                "type",
                "update_mode",
                "volume",
                "currency_code",
                "rchp",
                "rtc",
            ],
        )

        self.__send_message(
            "quote_add_symbols", [self.session_id, symbol,
                                  {"flags": ["force_permission"]}]
        )
        self.__send_message("quote_fast_symbols", [self.session_id, symbol])

        self.__send_message(
            "resolve_symbol",
            [
                self.chart_session,
                "symbol_1",
                '={"symbol":"'
                + symbol
                + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"')
                + "}",
            ],
        )
        self.__send_message(
            "create_series",
            [self.chart_session, "s1", "s1", "symbol_1", interval, n_bars],
        )
        self.__send_message("switch_timezone", [
                            self.chart_session, "exchange"])

        raw_data = ""

        logger.debug(f"getting data for {symbol}...")
        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except Exception as e:
                logger.error(e)
                break

            if "series_completed" in result:
                break

        return self.__create_df(raw_data, symbol)

    def search_symbol(self, text: str, exchange: str = ''):
        url = self.__search_url.format(text, exchange)
        print(" search --")
        symbols_list = []
        try:
            resp = requests.get(url)

            symbols_list = json.loads(resp.text.replace(
                '</em>', '').replace('<em>', ''))
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(e)

        return symbols_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tv = TvDatafeed()
    print(tv.get_hist("CRUDEOIL", "MCX", fut_contract=1))
    print(tv.get_hist("NIFTY", "NSE", fut_contract=1))
    print(
        tv.get_hist(
            "EICHERMOT",
            "NSE",
            interval=Interval.in_1_hour,
            n_bars=500,
            extended_session=False,
        )
    )
