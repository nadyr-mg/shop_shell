from payment_system_accounts.advcash import API_NAME, ACCOUNT_EMAIL, API_PASSWORD
from payment_system_libraries.AdvCash.soap_agent import SoapAgent

adv_agent = SoapAgent(API_NAME, ACCOUNT_EMAIL, API_PASSWORD)
for res in adv_agent.getBalances():
    res = str(res)
    print(res)
