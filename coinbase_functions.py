from coinbase.wallet.client import Client
from config import COINBASE_API_KEY, COINBASE_API_SECRET
from utils import to_satoshi, to_bitcoin

client = Client(COINBASE_API_KEY, COINBASE_API_SECRET, api_version="2017-10-26")
primary_account = client.get_primary_account()


def generate_address():
    return primary_account.create_address().address


def check(body, sign):
    return client.verify_callback(body, sign)


def send_money(address, amount, is_eng):
    balance = to_satoshi(float(primary_account.balance.amount))
    if amount > balance:
        if not is_eng:
            response = "Технические неполадки в платежной системе, попробуйте позже"
        else:
            response = "There is technical problems in payment system, try again later"
    else:
        primary_account.send_money(to=address, amount=str(to_bitcoin(amount)), currency="BTC")
        response = "Withdraw completed successfully!" if is_eng else "Вывод завершен успешно!"
    return response


if __name__ == "__main__":
    generate_address()
