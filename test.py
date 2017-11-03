# import config
#
# import binascii
# from hashlib import sha256
#
#
# def adjust_float(a):
#     a = str(a)
#     dot_idx = a.find('.')
#     if dot_idx == -1:
#         a += ".00"
#     elif len(a) - dot_idx - 1 < 2:
#         a += "0"
#     return a
#
#
# order_id = "12345"
# amount = 150
# amount = adjust_float(amount)
# desc = "Test payment №12345"
# desc = binascii.b2a_base64(desc.encode('utf8'))[:-1].decode()
# string_to_hash = ":".join(map(str, [config.PAYEER_MERCHANT_ID, order_id, amount, config.PAYEER_CURRENCY, desc,
#                                    config.PAYEER_SECRET_KEY]))
#
# res = sha256(string_to_hash.encode())
# res = res.hexdigest().upper()
#
# print(res)

import application


class Test:
    pass


message = Test()
message.chat = Test()
message.chat.id = 139263421
message.text = "300208162"
application.handle_reply_inviter(message)
