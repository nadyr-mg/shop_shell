import config
from utils import get_desc_sign

import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode, parse_qs

payment_systems = {
    'AdvCash': '87893285',
    'Payeer': '1136053',
    'Qiwi': '26808',
    'Yandex': '57378077'
}

base_values = {
    'account': config.PAYEER_ACCOUNT,
    'apiId': config.PAYEER_API_ID,
    'apiPass': config.PAYEER_API_KEY,
}

values_for_balance = dict(base_values)
values_for_balance['action'] = 'balance'

global_values = dict(base_values)
global_values['curIn'] = 'USD'
global_values['curOut'] = 'USD'

api_url = "https://payeer.com/ajax/api/api.php?{}"

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}


def init_values(pay_sys, requisite, amount):
    local_values = global_values
    local_values['ps'] = payment_systems[pay_sys]
    local_values['sumIn'] = amount
    local_values['param_ACCOUNT_NUMBER'] = requisite

    if pay_sys == 'Yandex':
        local_values['curOut'] = 'RUB'
    else:
        local_values['curOut'] = 'USD'
    return local_values


def get_balance():
    request = Request(api_url.format('balance'), data=urlencode(values_for_balance).encode(), headers=headers)

    response = json.loads(urlopen(request).read().decode())
    return round(float(response['balance']['USD']['BUDGET']) * config.BALANCE_USED_PART, 2)


# <editor-fold desc="Payout possibility">
def payout_possibility(pay_sys, requisite, amount, is_eng):
    balance = get_balance()
    if amount > balance:
        if not is_eng:
            result = "Технические неполадки в платежной системе, попробуйте позже"
        else:
            result = "There is technical problems in payment system, try again later"
        return result

    local_values = init_values(pay_sys, requisite, amount)
    local_values['action'] = 'initOutput'

    request = Request(api_url.format('initOutput'), data=urlencode(local_values).encode(), headers=headers)

    response = json.loads(urlopen(request).read().decode())
    errors = ""
    if (not isinstance(response['errors'], list) and response['errors'] is not None) \
            or (isinstance(response['errors'], list) and response['errors']):
        if not is_eng:
            errors += "Ошибки при обработке платежа:"
        else:
            errors += "Errors while performing payment:"
        errors += '\n'

        if isinstance(response['errors'], list):
            errors += '\n'.join(response['errors'])
        else:
            for key in response['errors']:
                if key == 'This type of exchange is not possible':
                    if not is_eng:
                        errors += "автоматический обмен из {} в {} временно запрещен".format(local_values['curIn'],
                                                                                             local_values['curOut'])
                    else:
                        errors += response['errors'][key]
                    errors += '\n'
                elif response['errors'][key] == 'invalid format':
                    if not is_eng:
                        errors += "неправильный формат реквизита"
                    else:
                        errors += "invalid requisite format"
                    errors += '\n'
                elif key == 'sum_more_max':
                    if not is_eng:
                        errors += "сумма превышает максимум"
                    else:
                        errors += response['errors'][key]
                    errors += '\n'
                elif key == 'sum_less_min':
                    if not is_eng:
                        temp = "минимальная сумма перевода: *{} {}*"
                    else:
                        temp = "minimal amount for transaction is *{} {}*"
                    errors += temp.format(response['errors'][key][12:], local_values['curOut']) + '\n'
    return errors


# </editor-fold>


# <editor-fold desc="Payout">
def payout(pay_sys, requisite, amount, is_eng):
    local_values = init_values(pay_sys, requisite, amount)
    local_values['action'] = 'output'

    request = Request(api_url.format('output'), data=urlencode(local_values).encode(), headers=headers)

    response = json.loads(urlopen(request).read().decode())
    if (not isinstance(response['errors'], list) and response['errors'] is not None and response['errors']) \
            or (isinstance(response['errors'], list) and response['errors']):
        if is_eng:
            result = "Something went wrong. Check validity of your requisites or try again later"
        else:
            result = "Что-то пошло не так. Проверьте правильность введеных реквизитов или повторите попытку позднее"
    else:
        result = "Withdraw completed successfully!" if is_eng else "Вывод завершен успешно!"
    return result


# </editor-fold>


def create_merchant(order_id, order_email, amount):
    local_values = dict(base_values)
    local_values['action'] = 'merchant'
    desc, sign = get_desc_sign(order_id, amount)
    local_values['shop'] = {
        'm_shop': config.PAYEER_MERCHANT_ID,
        'm_orderid': order_id,
        'm_amount': amount,
        'm_curr': config.PAYEER_CURRENCY,
        'm_desc': desc,
        'm_sign': sign
    }
    local_values['shop'] = json.dumps(local_values['shop'])
    local_values['ps'] = {
        'id': '20916096',
        'curr': config.PAYEER_CURRENCY
    }
    local_values['ps'] = json.dumps(local_values['ps'])
    local_values['form'] = {
        'order_email': order_email
    }
    local_values['form'] = json.dumps(local_values['form'])
    local_values['status_url'] = config.PAYEER_STATUS_URL

    local_values = urlencode(local_values).encode()
    l = parse_qs(local_values)
    request = Request(api_url.format('merchant'), data=local_values, headers=headers)

    response = json.loads(urlopen(request).read().decode())

    return response


if __name__ == '__main__':
    print(create_merchant('fsd4bdrg', 'lester0578@gmail.com', 100.00))
    # import binascii
    # from hashlib import sha256
    #
    # amount = "1.00"
    # order_id = "12345"
    # desc = "Test"
    # desc = binascii.b2a_base64(desc.encode('utf8'))[:-1].decode()
    # string_to_hash = ":".join(map(str, ["12345", order_id, amount, config.PAYEER_CURRENCY, desc,
    #                                     'Секретный ключ']))
    # hash = sha256(string_to_hash.encode()).hexdigest().upper()
    print()
