import hashlib
import os

import config

from urllib.request import urlopen, Request
from urllib.parse import urlencode

from Data_base.user_db_class import Users_db

data = {"id": "86ede88e-27b6-5134-b691-668e62591833",
        "type": "wallet:addresses:new-payment",
        "data": {
            "id": "cba3e3ad-f0a5-5fb6-b966-43531c0001b7",
            "address": "1F2T9wyUFAxushFzdY4tyPmNdgsykoj4SD",
            "name": None,
            "created_at": "2017-11-07T19:26:05Z",
            "updated_at": "2017-11-07T19:26:05Z",
            "network": "bitcoin",
            "resource": "address",
            "resource_path": "/v2/accounts/d4eca3a7-21ab-5528-bcb6-62278fab6e9a/addresses/cba3e3ad-f0a5-5fb6-b966-43531c0001b7"
        },
        "user": {
            "id": "495207d9-0c07-5bd3-96c4-9995e792c7c1",
            "resource": "user",
            "resource_path": "/v2/users/495207d9-0c07-5bd3-96c4-9995e792c7c1"
        },
        "account": {
            "id": "d4eca3a7-21ab-5528-bcb6-62278fab6e9a",
            "resource": "account", "resource_path": "/v2/accounts/d4eca3a7-21ab-5528-bcb6-62278fab6e9a"
        },
        "delivery_attempts": 1,
        "created_at": "2017-11-07T19:36:31Z",
        "resource": "notification",
        "resource_path": "/v2/notifications/86ede88e-27b6-5134-b691-668e62591833",
        "additional_data": {
            "hash": "b3503b81e2b3289f6220cca8c6758e1a6f9a020e273f46ff4fad8ec33b584016",
            "amount": {
                "amount": "0.00000546",
                "currency": "BTC"
            },
            "transaction": {
                "id": "fcf87286-1687-52a6-b227-e991425601dc",
                "resource": "transaction",
                "resource_path": "/v2/accounts/d4eca3a7-21ab-5528-bcb6-62278fab6e9a/transactions/fcf87286-1687-52a6-b227-e991425601dc"
            }
        }
        }

data2 = {'id': '9cc34159-fb8c-5dc8-8810-43d722df1ac2', 'type': 'wallet:addresses:new-payment',
         'data': {'id': 'e4639c88-936b-5c49-9e87-45c366c3e81b', 'address': '1HRSPpNqDC44NuaUXiay2Hi7N1ksu7ShzH',
                  'name': None, 'created_at': '2017-11-10T07:53:40Z', 'updated_at': '2017-11-10T07:53:40Z',
                  'network': 'bitcoin', 'resource': 'address',
                  'resource_path': '/v2/accounts/d4eca3a7-21ab-5528-bcb6-62278fab6e9a/addresses/e4639c88-936b-5c49-9e87-45c366c3e81b'},
         'user': {'id': '495207d9-0c07-5bd3-96c4-9995e792c7c1', 'resource': 'user',
                  'resource_path': '/v2/users/495207d9-0c07-5bd3-96c4-9995e792c7c1'},
         'account': {'id': 'd4eca3a7-21ab-5528-bcb6-62278fab6e9a', 'resource': 'account',
                     'resource_path': '/v2/accounts/d4eca3a7-21ab-5528-bcb6-62278fab6e9a'}, 'delivery_attempts': 0,
         'created_at': '2017-11-10T07:55:12Z', 'resource': 'notification',
         'resource_path': '/v2/notifications/9cc34159-fb8c-5dc8-8810-43d722df1ac2',
         'additional_data': {'hash': 'dbfb4c716cfb688220e48dd139415ca9c1b7b2d4bad09564c3721cf8a8e30de9',
                             'amount': {'amount': '0.00000705', 'currency': 'BTC'},
                             'transaction': {'id': 'a0fb3414-daf6-5c80-bc49-cb103501e862', 'resource': 'transaction',
                                             'resource_path': '/v2/accounts/d4eca3a7-21ab-5528-bcb6-62278fab6e9a/transactions/a0fb3414-daf6-5c80-bc49-cb103501e862'}}}
from Data_base.user_db_class import Users_db

users_db = Users_db(config.DB_NAME)
user_id = users_db.select_addr_user("1HRSPpNqDC44NuaUXiay2Hi7N1ksu7ShzH")
users_db.close()

print()
