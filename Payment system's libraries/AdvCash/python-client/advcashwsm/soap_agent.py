#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
from datetime import datetime
from pysimplesoap.client import SoapClient, soap_namespaces, sort_dict

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

    def __init__(self, api_name, account_email, api_password):
        self.api_name = api_name
        self.account_email = account_email
        self.api_password = api_password

        self.client = SoapClient(location=self.WSDL_URL, wsdl=self.WSDL_URL, ns="wsm")
        self.arg0 = {
            "apiName": self.api_name,
            "authenticationToken": self.getAuthenticationToken(self.api_password),
            "accountEmail": self.account_email
        }

    def getAuthenticationToken(self, password):
        currentUTCDate = datetime.utcnow().strftime("%Y%m%d:%H")
        return hashlib.sha256(password + ":" + currentUTCDate).hexdigest()

    def register(self, registrationData):
        return self.client.register(arg0 = self.arg0, arg1 = registrationData)

    def emailTransfer(self, transaction):
        return self.client.emailTransfer(arg0 = self.arg0, arg1 = transaction)

    def findTransaction(self, transactionId):
        return self.client.findTransaction(arg0 = self.arg0, arg1 = transactionId)

    def getBalances(self):
        return self.client.getBalances(arg0 = self.arg0)

    def history(self, history_filter):
        return self.client.history(arg0 = self.arg0, arg1 = history_filter)

    def makeCurrencyExchange(self, transaction, isAmountInSrcWalletCurrency):
        return self.client.makeCurrencyExchange(arg0 = self.arg0,
                                                arg1 = transaction,
                                                arg2 = isAmountInSrcWalletCurrency)

    def validationCurrencyExchange(self, transaction):
        return self.client.validationCurrencyExchange(arg0 = self.arg0,
                                                      arg1 = transaction)

    def currencyExchange(self, transaction):
        return self.client.currencyExchange(arg0 = self.arg0,
                                                arg1 = transaction)

    def makeTransfer(self, transfer_type, transaction):
        return self.client.makeTransfer(arg0 = self.arg0,
                                        arg1 = transfer_type,
                                        arg2 = transaction)

    def transferAdvcashCard(self, transaction):
        return self.client.transferAdvcashCard(arg0 = self.arg0,
                                               arg1 = transaction)

    def transferBankCard(self, transaction):
        return self.client.transferBankCard(arg0 = self.arg0,
                                            arg1 = transaction)

    def validateAccount(self, account):
        return self.client.validateAccount(arg0 = self.arg0,
                                           arg1 = account)

    def validateAccounts(self, accounts):
        args = [("arg0", self.arg0)]
        for account in accounts:
            args.append(("arg1", account))

        method = "validateAccounts"

        soap_uri = soap_namespaces['soapenv']
        operation = self.client.get_operation(method)

        # get i/o type declarations:
        output = operation['output']
        header = operation.get('header')
        if 'action' in operation:
            self.client.action = operation['action']

        # construct header and parameters
        if header:
            self.client.__call_headers = sort_dict(header, self.client.__headers)

        # call remote procedure
        response = self.client.call(method, *args)
        # parse results:
        resp = response('Body', ns=soap_uri).children().unmarshall(output)
        return resp and list(resp.values())[0]  # pass Response tag children

    def validateAdvcashCardTransfer(self, transaction):
        return self.client.validateAdvcashCardTransfer(arg0 = self.arg0,
                                           arg1 = transaction)

    def validateBankCardTransfer(self, transaction):
        return self.client.validateBankCardTransfer(arg0 = self.arg0,
                                           arg1 = transaction)

    def validateCurrencyExchange(self, transaction):
        return self.client.validateCurrencyExchange(arg0 = self.arg0,
                                           arg1 = transaction)

    def validateEmailTransfer(self, transaction):
        return self.client.validateEmailTransfer(arg0 = self.arg0,
                                           arg1 = transaction)

    def validateTransfer(self, transaction_type, transaction):
        return self.client.validateTransfer(arg0 = self.arg0,
                                            arg1 = transaction_type,
                                           arg2 = transaction)

    def validateWithdrawalThroughExternalPaymentSystem(self, transaction):
        return self.client.validateWithdrawalThroughExternalPaymentSystem(arg0 = self.arg0,
                                            arg1 = transaction)

    def withdrawalThroughExternalPaymentSystem(self, transaction):
        return self.client.withdrawalThroughExternalPaymentSystem(arg0 = self.arg0,
                                            arg1 = transaction)

    def validationSendMoney(self, sendMoneyData):
        return self.client.validationSendMoney(arg0 = self.arg0,
                                               arg1 = sendMoneyData)

    def sendMoney(self, sendMoneyData):
        return self.client.sendMoney(arg0 = self.arg0,
                                     arg1 = sendMoneyData)

    def validationSendMoneyToAdvcashCard(self, sendMoneyToAdvcashCardData):
        return self.client.validationSendMoneyToAdvcashCard(arg0 = self.arg0,
                                                            arg1 = sendMoneyToAdvcashCardData)

    def sendMoneyToAdvcashCard(self, sendMoneyToAdvcashCardData):
        return self.client.sendMoneyToAdvcashCard(arg0 = self.arg0,
                                                  arg1 = sendMoneyToAdvcashCardData)

    def validationSendMoneyToBankCard(self, sendMoneyToBankCardData):
        return self.client.validationSendMoneyToBankCard(arg0 = self.arg0,
                                                         arg1 = sendMoneyToBankCardData)

    def sendMoneyToBankCard(self, sendMoneyToBankCardData):
        return self.client.sendMoneyToBankCard(arg0 = self.arg0,
                                               arg1 = sendMoneyToBankCardData)

    def validationSendMoneyToEcurrency(self, sendMoneyToEcurrencyData):
        return self.client.validationSendMoneyToEcurrency(arg0 = self.arg0,
                                                          arg1 = sendMoneyToEcurrencyData)

    def sendMoneyToEcurrency(self, sendMoneyToEcurrencyData):
        return self.client.sendMoneyToEcurrency(arg0 = self.arg0,
                                                arg1 = sendMoneyToEcurrencyData)

    def validationSendMoneyToEmail(self, sendMoneyToEmailData):
        return self.client.validationSendMoneyToEmail(arg0 = self.arg0,
                                                      arg1 = sendMoneyToEmailData)

    def sendMoneyToEmail(self, sendMoneyToEmailData):
        return self.client.sendMoneyToEmail(arg0 = self.arg0,
                                            arg1 = sendMoneyToEmailData)
