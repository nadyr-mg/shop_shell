from os import environ

TOKEN = ""
BOT_USERNAME = ""
HOST_ID = 139263421  # Your id in telegram
TRUSTED_IDs = [HOST_ID]

DB_NAME = "Data_base/User_statistics.db"

SERVER_IP = ''
WEBHOOK_DOMAIN = ""

WEBHOOK_PORT = int(environ.get('PORT', '8443'))
WEBHOOK_LISTEN = '0.0.0.0'

# <editor-fold desc="Payeer info">
# <editor-fold desc="Merchant">
PAYEER_CONFIRM = ""

PAYEER_SECRET_KEY = ""
PAYEER_ADDITIONAL_KEY = ""

PAYEER_MERCHANT_ID = ""
PAYEER_CURRENCY = "USD"
PAYEER_PAY_DESC = "Пополнение счета в Trade bot"

PAYEER_TRUSTED_IPS = ['185.71.65.92', '185.71.65.189', '149.202.17.210']
# </editor-fold>

# <editor-fold desc="Payeer API">
PAYEER_ACCOUNT = ""
PAYEER_API_KEY = ""
PAYEER_API_ID = ""

PAYEER_STATUS_URL = "https://{}/check.php".format(WEBHOOK_DOMAIN)
# </editor-fold>
# </editor-fold>

# <editor-fold desc="Coinbase info">
COINBASE_API_KEY = ""
COINBASE_API_SECRET = ""
# </editor-fold>

MIN_REFILL_USD = 0.1
MIN_REFILL_BTC = int(0.000006 * 100000000)
MIN_WITHDRAW_USD = 0.1
MIN_WITHDRAW_BTC = int(0.000006 * 100000000)

BALANCE_USED_PART = 0.8

BTC_AVER_TRANSCTION_SIZE = 226
BTC_FEE_MULT = 1.2

ABOUT_TEXT = ("сампл текст",
              "sample text"
              )
