# Importing libraries
from binance.client import Client
import configparser
import nest_asyncio
nest_asyncio.apply()

# loading keys from config file
config = configparser.ConfigParser()
config.read_file(open('C:/Users/louis/Documents/CryptoTrading/keys.cfg'))
# Effective Account
#test_api_key = config.get('BINANCE', 'ACTUAL_API_KEY')
#test_secret_key = config.get('BINANCE', 'ACTUAL_SECRET_KEY')
# Test Account Spot
test_api_key = config.get('BINANCE', 'TEST_API_KEY')
test_secret_key = config.get('BINANCE', 'TEST_SECRET_KEY')
# Test Account Futures
#test_api_key = config.get('BINANCE', 'TESTFUTURE_API_KEY')
#test_secret_key = config.get('BINANCE', 'TESTFUTURE_SECRET_KEY')

client = Client(test_api_key, test_secret_key, testnet=False)