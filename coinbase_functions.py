from coinbase.wallet.client import Client
from coinbase.wallet.error import APIError
from requests import request
from json import loads

from config import COINBASE_API_KEY, COINBASE_API_SECRET, BALANCE_USED_PART, BTC_AVER_TRANSCTION_SIZE, BTC_FEE_MULT
from utils import to_satoshi, to_bitcoin

client = Client(COINBASE_API_KEY, COINBASE_API_SECRET, api_version="2017-10-26")
primary_account = client.get_primary_account()


def generate_address():
    return primary_account.create_address().address


def check(body, headers):
    if 'HTTP_CB_SIGNATURE' in headers:
        sign = headers['HTTP_CB_SIGNATURE']
    else:
        return False
    return client.verify_callback(body, sign)


def get_balance():
    return to_satoshi(float(primary_account.balance.amount) * BALANCE_USED_PART)


def get_cur_fee():
    res = request("GET", "https://bitcoinfees.earn.com/api/v1/fees/recommended").text
    return loads(res)['fastestFee'] * BTC_AVER_TRANSCTION_SIZE * BTC_FEE_MULT


def send_money(address, amount, is_eng):
    balance = get_balance()
    if amount > balance:
        if not is_eng:
            response = "Технические неполадки в платежной системе, попробуйте позже"
        else:
            response = "There is technical problems in payment system, try again later"
    else:
        cur_fee = get_cur_fee()
        if amount <= cur_fee:
            response = "Amount is below the fee" if is_eng else "Сумма вывода меньше коммисии"
        else:
            amount -= cur_fee
            try:
                primary_account.send_money(to=address, amount="{:.8f}".format(to_bitcoin(amount)), currency="BTC")
            except APIError as e:
                error = str(e)
                semicolon = error.find(':')
                if semicolon == -1:
                    if is_eng:
                        response = "Something went wrong. Check validity of your requisites or try again later"
                    else:
                        response = "Что-то пошло не так. Проверьте правильность введеных реквизитов или повторите " \
                                   "попытку позднее "
                else:
                    response = error[semicolon + 1:]
            else:
                response = "Withdraw completed successfully!" if is_eng else "Вывод завершен успешно!"
    return response


if __name__ == "__main__":
    primary_account.send_money(to="17g2zDvvMtZKSSfjqN1Jiudmq9dTANwQvu", amount="0.0001", currency="BTC",
                               fee="0.0000226")

