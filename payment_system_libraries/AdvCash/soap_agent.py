#!/usr/bin/python
# -*- coding: utf-8 -*-

from builtins import object
import hashlib
from datetime import datetime
from zeep import Client

CURRENCY_EXCHANGE_ACTION_BUY = "BUY"
CURRENCY_EXCHANGE_ACTION_SELL = "SELL"

CURRENCY_USD = "USD"
CURRENCY_EUR = "EUR"
CURRENCY_RUR = "RUR"
CURRENCY_GBP = "GBP"

SUPPORTED_LANGUAGE_EN = "en"
SUPPORTED_LANGUAGE_RU = "ru"

BITCOIN = "BITCOIN"
OK_PAY = "OK_PAY"
PAXUM = "PAXUM"
PAYEER = "PAYEER"
YANDEX_MONEY = "YANDEX_MONEY"

CARD_TYPE_VIRTUAL = "VIRTUAL"
CARD_TYPE_PLASTIC = "PLASTIC"


class SoapAgent(object):
    WSDL_URL = "https://wallet.advcash.com/wsm/merchantWebService?wsdl"
    WSDL_LOCATION = "https://wallet.advcash.com/wsm/merchantWebService"

    def __init__(self, api_name, account_email, api_password):
        self.api_name = api_name
        self.account_email = account_email
        self.api_password = api_password

        self.client = Client(wsdl=self.WSDL_URL)
        self.arg0 = {
            "apiName": self.api_name,
            "authenticationToken": self.getAuthenticationToken(self.api_password),
            "accountEmail": self.account_email
        }

    def getAuthenticationToken(self, password):
        currentUTCDate = datetime.utcnow().strftime("%Y%m%d:%H")
        s = password + ":" + currentUTCDate
        return hashlib.sha256(s.encode()).hexdigest()

    def register(self, registrationData):
        return self.client.service.register(arg0=self.arg0, arg1=registrationData)

    def emailTransfer(self, transaction):
        return self.client.service.emailTransfer(arg0=self.arg0, arg1=transaction)

    def findTransaction(self, transactionId):
        return self.client.service.findTransaction(arg0=self.arg0, arg1=transactionId)

    def getBalances(self):
        return self.client.service.getBalances(arg0=self.arg0)

    def history(self, history_filter):
        return self.client.service.history(arg0=self.arg0, arg1=history_filter)

    def makeCurrencyExchange(self, transaction, isAmountInSrcWalletCurrency):
        return self.client.service.makeCurrencyExchange(arg0=self.arg0,
                                                arg1=transaction,
                                                arg2=isAmountInSrcWalletCurrency)

    def validationCurrencyExchange(self, transaction):
        return self.client.service.validationCurrencyExchange(arg0=self.arg0,
                                                      arg1=transaction)

    def currencyExchange(self, transaction):
        return self.client.service.currencyExchange(arg0=self.arg0,
                                            arg1=transaction)

    def makeTransfer(self, transfer_type, transaction):
        return self.client.service.makeTransfer(arg0=self.arg0,
                                        arg1=transfer_type,
                                        arg2=transaction)

    def transferAdvcashCard(self, transaction):
        return self.client.service.transferAdvcashCard(arg0=self.arg0,
                                               arg1=transaction)

    def transferBankCard(self, transaction):
        return self.client.service.transferBankCard(arg0=self.arg0,
                                            arg1=transaction)

    def validateAccount(self, account):
        return self.client.service.validateAccount(arg0=self.arg0,
                                           arg1=account)

    def validateAccounts(self, **kwargs):
        return self.client.service.validateAccounts(arg0=self.arg0, **kwargs)

    def validateAdvcashCardTransfer(self, transaction):
        return self.client.service.validateAdvcashCardTransfer(arg0=self.arg0,
                                                       arg1=transaction)

    def validateBankCardTransfer(self, transaction):
        return self.client.service.validateBankCardTransfer(arg0=self.arg0,
                                                    arg1=transaction)

    def validateCurrencyExchange(self, transaction):
        return self.client.service.validateCurrencyExchange(arg0=self.arg0,
                                                    arg1=transaction)

    def validateEmailTransfer(self, transaction):
        return self.client.service.validateEmailTransfer(arg0=self.arg0,
                                                 arg1=transaction)

    def validateTransfer(self, transaction_type, transaction):
        return self.client.service.validateTransfer(arg0=self.arg0,
                                            arg1=transaction_type,
                                            arg2=transaction)

    def validateWithdrawalThroughExternalPaymentSystem(self, transaction):
        return self.client.service.validateWithdrawalThroughExternalPaymentSystem(arg0=self.arg0,
                                                                          arg1=transaction)

    def withdrawalThroughExternalPaymentSystem(self, transaction):
        return self.client.service.withdrawalThroughExternalPaymentSystem(arg0=self.arg0,
                                                                  arg1=transaction)

    def validationSendMoney(self, sendMoneyData):
        return self.client.service.validationSendMoney(arg0=self.arg0,
                                               arg1=sendMoneyData)

    def sendMoney(self, sendMoneyData):
        return self.client.service.sendMoney(arg0=self.arg0,
                                     arg1=sendMoneyData)

    def validationSendMoneyToAdvcashCard(self, sendMoneyToAdvcashCardData):
        return self.client.service.validationSendMoneyToAdvcashCard(arg0=self.arg0,
                                                            arg1=sendMoneyToAdvcashCardData)

    def sendMoneyToAdvcashCard(self, sendMoneyToAdvcashCardData):
        return self.client.service.sendMoneyToAdvcashCard(arg0=self.arg0,
                                                  arg1=sendMoneyToAdvcashCardData)

    def validationSendMoneyToBankCard(self, sendMoneyToBankCardData):
        return self.client.service.validationSendMoneyToBankCard(arg0=self.arg0,
                                                         arg1=sendMoneyToBankCardData)

    def sendMoneyToBankCard(self, sendMoneyToBankCardData):
        return self.client.service.sendMoneyToBankCard(arg0=self.arg0,
                                               arg1=sendMoneyToBankCardData)

    def validationSendMoneyToEcurrency(self, sendMoneyToEcurrencyData):
        return self.client.service.validationSendMoneyToEcurrency(arg0=self.arg0,
                                                          arg1=sendMoneyToEcurrencyData)

    def sendMoneyToEcurrency(self, sendMoneyToEcurrencyData):
        return self.client.service.sendMoneyToEcurrency(arg0=self.arg0,
                                                arg1=sendMoneyToEcurrencyData)

    def validationSendMoneyToEmail(self, sendMoneyToEmailData):
        return self.client.service.validationSendMoneyToEmail(arg0=self.arg0,
                                                      arg1=sendMoneyToEmailData)

    def sendMoneyToEmail(self, sendMoneyToEmailData):
        return self.client.service.sendMoneyToEmail(arg0=self.arg0,
                                            arg1=sendMoneyToEmailData)
