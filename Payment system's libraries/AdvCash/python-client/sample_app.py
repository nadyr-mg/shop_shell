#!/usr/bin/python
# -*- coding: utf-8 -*-

from decimal import *
import warnings
warnings.filterwarnings('ignore')

#import logging
#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

from advcashwsm.soap_agent import SoapAgent
from advcashwsm.soap_agent import CURRENCY_USD, CURRENCY_EUR, CURRENCY_RUR
from advcashwsm.soap_agent import CURRENCY_EXCHANGE_ACTION_SELL
from advcashwsm.soap_agent import SUPPORTED_LANGUAGE_EN
from advcashwsm.soap_agent import YANDEX_MONEY
from advcashwsm.soap_agent import CARD_TYPE_VIRTUAL

api_name = "api_name"
account_email = "bolkimen@insart.com"
api_password = "password"


sa = SoapAgent(api_name, account_email, api_password)

## getBalances
print "getBalances"
for balance in sa.getBalances():
    print "\t%s\t->\t%s" % ( balance['return']['id'], balance['return']['amount'] )
print

## emailTransfer
#print sa.emailTransfer({"amount": Decimal('5.00'),
#                           "comment": "test payment",
#                           "destCurrency": CURRENCY_USD,
#                           "email": "someuser@example.com",
#                           "srcWalletId": "U944079833602"})

## findTransaction
#print sa.findTransaction("fd6e2b9d-5f3e-4f5c-9127-3ea215225df7")

## history
print "history"
for history in sa.history({}):
    print history
print

## register
#print sa.register({"email": "some@mail.com",
#                   "firstName": "FirstName",
#                   "lastName": "LastName",
#                   "language": SUPPORTED_LANGUAGE_EN,
#                   "ip": "*.*.*.*"})

## validationCurrencyExchange
#sa.validationCurrencyExchange({"from": CURRENCY_EUR,
#                               "to": CURRENCY_USD,
#                               "action": CURRENCY_EXCHANGE_ACTION_SELL,
#                               "amount": Decimal("5.00"),
#                               "note": "sell some"})

## currencyExchange
#print sa.currencyExchange({"from": CURRENCY_EUR,
#                     "to": CURRENCY_USD,
#                     "action": CURRENCY_EXCHANGE_ACTION_SELL,
#                     "amount": Decimal("5.00"),
#                     "note": "sell some"})

## validateAccount
#print sa.validateAccount({"email": "someuser@example.com",
#                          "walletId": "U000000000000",
#                          "firstName": "Petya",
#                          "lastName": "Pupkin"})

## validateAccounts
print "validateAccounts"
for account in sa.validateAccounts(["pupkin", "petya", "bob"]):
    print "\t%s\t->\t%s" % ( account["return"]["systemAccountName"], account["return"]["present"] )
print

## validationSendMoney
#sa.validationSendMoney({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "email": "receiver@mail.com",
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## sendMoney
#sa.sendMoney({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "email": "receiver@mail.com",
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## validationSendMoneyToAdvcashCard
#sa.validationSendMoneyToAdvcashCard({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "email": "receiver@mail.com",
#                        "cardType": CARD_TYPE_VIRTUAL,
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## sendMoneyToAdvcashCard
#sa.sendMoneyToAdvcashCard({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "email": "receiver@mail.com",
#                        "cardType": CARD_TYPE_VIRTUAL,
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## validationSendMoneyToBankCard
#sa.validationSendMoneyToBankCard({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "cardNumber": "visa_or_mastercard_card_number",
#                        "expiryMonth": "01",
#                        "expiryYear": "19",
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## sendMoneyToBankCard
#sa.sendMoneyToBankCard({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "cardNumber": "visa_or_mastercard_card_number",
#                        "expiryMonth": "01",
#                        "expiryYear": "19",
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## validationSendMoneyToEcurrency
#sa.validationSendMoneyToEcurrency({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_RUR,
#                        "ecurrency": YANDEX_MONEY,
#                        "receiver": "receiver",
#                        "note": "some useful information",
#                        "savePaymentTemplate": False})

## sendMoneyToEcurrency
#sa.sendMoneyToEcurrency({"amount": Decimal("5.00"),
#                         "currency": CURRENCY_RUR,
#                         "ecurrency": YANDEX_MONEY,
#                         "receiver": "receiver",
#                         "note": "some useful information",
#                         "savePaymentTemplate": False})

## validationSendMoneyToEmail
#sa.validationSendMoneyToEmail({"amount": Decimal("5.00"),
#                        "currency": CURRENCY_USD,
#                        "email": "receiver@mail.com",
#                        "note": "some useful information"})

## sendMoneyToEmail
#sa.sendMoneyToEmail({"amount": Decimal("5.00"),
#                     "currency": CURRENCY_USD,
#                     "email": "receiver@mail.com",
#                     "note": "some useful information"})
