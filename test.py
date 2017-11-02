import config

import binascii
from hashlib import sha256

order_id = "12345"
amount = 150
desc = "Test payment №12345"
desc = binascii.b2a_base64(desc.encode('utf8'))[:-1]
string_to_hash = ":".join(map(str, [config.PAYEER_MERCHANT_ID, order_id, amount, config.PAYEER_CURRENCY, desc,
                                   config.PAYEER_SECRET_KEY]))

res = sha256(string_to_hash.encode())
res = res.hexdigest().upper()

print()

# FIXME: sign that I'm getting is not equal to one that Payeer want

