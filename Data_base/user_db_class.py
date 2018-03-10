import sqlite3
from time import time


class Users_db:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, isolation_level=None)
        self.cursor = self.connection.cursor()

    # <editor-fold desc="Statistics table">
    def select_stats_all(self):
        return self.cursor.execute('SELECT * FROM Statistics').fetchall()

    def select_stats(self, user_id):
        return self.cursor.execute('SELECT * FROM Statistics WHERE user_id = ?', (user_id,)).fetchone()

    def select_stats_field(self, user_id, field):
        return self.cursor.execute('SELECT {} FROM Statistics WHERE user_id = ?'.format(field), (user_id,)).fetchone()[0]

    def select_stats_users(self):
        return self.cursor.execute('SELECT user_id, income, income_btc, is_eng FROM Statistics').fetchall()

    def select_stats_users_id(self):
        return self.cursor.execute('SELECT user_id FROM Statistics').fetchall()

    def select_stats_income(self, user_id):
        return self.cursor.execute('SELECT income, income_btc FROM Statistics WHERE user_id = ?', (user_id,)).fetchone()

    def is_exist_stats(self, user_id):
        return self.cursor.\
            execute('SELECT EXISTS(SELECT user_id FROM Statistics WHERE user_id = ?)', (user_id,)).fetchone()[0]

    def insert_stats(self, data):
        self.cursor.execute('INSERT INTO Statistics VALUES(?, ?, ?, ?, ?, ?, ?, ?)', data)

    def update_stats_field(self, user_id, field, value):
        self.cursor.execute("""UPDATE Statistics SET 
                                  "{}" = ?
                                WHERE user_id = ?""".format(field), (value, user_id))

    def update_stats_add_income(self, user_id):
        self.cursor.execute("""UPDATE Statistics SET 
                                  "balance" = "balance" + "income",
                                  "balance_btc" = "balance_btc" + "income_btc"
                                WHERE user_id = ?""", (user_id,))

    def update_stats_add_to_balance(self, user_id, value, is_btc=0):
        field = "balance"
        if is_btc:
            field += "_btc"
        self.cursor.execute("""UPDATE Statistics SET 
                                  "{}" = "{}" + ?
                                WHERE user_id = ?""".format(field, field), (value, user_id))

    def update_stats_dec_balance(self, user_id, value, is_btc=0):
        field = "balance"
        if is_btc:
            field += "_btc"
        self.cursor.execute("""UPDATE Statistics SET 
                                  "{}" = "{}" - ?
                                WHERE user_id = ?""".format(field, field), (value, user_id))

    def update_stats_invested(self, user_id, invested, income):
        self.cursor.execute("""UPDATE Statistics SET 
                                  "invested" = ?,
                                  "income" = ?
                                WHERE user_id = ?""", (invested, income, user_id))

    def update_stats_invested_btc(self, user_id, invested_btc, income_btc):
        self.cursor.execute("""UPDATE Statistics SET 
                                  "invested_btc" = ?,
                                  "income_btc" = ?
                                WHERE user_id = ?""", (invested_btc, income_btc, user_id))

    def update_stats_nullify_balance(self, user_id):
        self.cursor.execute("""UPDATE Statistics SET 
                                  "balance" = 0
                                WHERE user_id = ?""", (user_id,))

    def update_stats_nullify_balance_btc(self, user_id):
        self.cursor.execute("""UPDATE Statistics SET 
                                  "balance_btc" = 0
                                WHERE user_id = ?""", (user_id,))
    # </editor-fold>

    # <editor-fold desc="Ref_program table">
    def select_ref_all_all(self):
        return self.cursor.execute('SELECT * FROM Ref_program').fetchall()

    def select_ref_all(self, user_id):
        return self.cursor.execute('SELECT * FROM Ref_program WHERE user_id = ?', (user_id,)).fetchone()

    def select_ref_inviter(self, user_id):
        return self.cursor.execute('SELECT inviter FROM Ref_program WHERE user_id = ?', (user_id,)).fetchone()[0]

    def insert_ref(self, user_id):
        self.cursor.execute('INSERT INTO Ref_program VALUES(?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 0)', (user_id,))

    def update_ref_people_count(self, user_id, line_number, operation):
        people_name = str(line_number) + "_people"
        self.cursor.execute("""UPDATE Ref_program SET 
                                  "{}" = "{}" {} 1
                                WHERE user_id = ?""".format(people_name, people_name, operation), (user_id,))

    def update_ref_inviter(self, user_id, inviter):
        self.cursor.execute("""UPDATE Ref_program SET 
                                  "inviter" = ?
                                WHERE user_id = ?""", (inviter, user_id))

    def update_ref_line(self, user_id, line_number, line_value):
        line_name = str(line_number) + "_line"
        self.cursor.execute("""UPDATE Ref_program SET 
                                  "{}" = IFNULL("{}", 0) + ?
                                WHERE user_id = ?""".format(line_name, line_name), (line_value, user_id))

    def update_ref_line_btc(self, user_id, line_number, line_value_btc):
        line_name = str(line_number) + "_line_btc"
        self.cursor.execute("""UPDATE Ref_program SET 
                                  "{}" = IFNULL("{}", 0) + ?
                                WHERE user_id = ?""".format(line_name, line_name), (line_value_btc, user_id))
    # </editor-fold>

    # <editor-fold desc="Salts table">
    def select_salts_all(self):
        return self.cursor.execute('SELECT * FROM Salts').fetchall()

    def select_salts_user_id(self, salt):
        return self.cursor.execute('SELECT user_id FROM Salts WHERE salt = ?', (salt,)).fetchone()

    def select_salt(self, user_id):
        return self.cursor.execute('SELECT salt FROM Salts WHERE user_id = ?', (user_id,)).fetchone()

    def insert_salt(self, salt, user_id):
        try:
            self.cursor.execute('INSERT INTO Salts VALUES(?, ?)', (salt, user_id))
        except sqlite3.IntegrityError:
            return False
        return True
    # </editor-fold>

    # <editor-fold desc="Requisites table">
    def select_requisites_all(self):
        return self.cursor.execute('SELECT * FROM Requisites').fetchall()

    def select_requisites(self, user_id):
        return self.cursor.execute('SELECT * FROM Requisites WHERE user_id = ?', (user_id,)).fetchone()

    def select_requisite(self, user_id, requisite_name):
        return self.cursor.execute('SELECT {} FROM Requisites WHERE user_id = ?'.format(requisite_name),
                                   (user_id,)).fetchone()[0]

    def is_exist_requisites(self, user_id):
        return self.cursor.\
            execute('SELECT EXISTS(SELECT user_id FROM Requisites WHERE user_id = ?)', (user_id,)).fetchone()[0]

    def insert_requisites(self, user_id):
        self.cursor.execute('INSERT INTO Requisites VALUES(?, NULL, NULL, NULL, NULL, NULL)', (user_id,))

    def update_requisite(self, user_id, requisite_name, requisite):
        self.cursor.execute("""UPDATE Requisites SET 
                                  "{}" = ?
                                WHERE user_id = ?""".format(requisite_name), (requisite, user_id))
    # </editor-fold>

    # <editor-fold desc="Replenishments table">
    def select_repl_all(self):
        return self.cursor.execute('SELECT * FROM Replenishments').fetchall()

    def select_repl_user(self, order_id):
        return self.cursor.execute('SELECT user_id FROM Replenishments WHERE order_id = ?', (order_id,)).fetchone()[0]

    def select_repl_amount(self, order_id):
        return self.cursor.execute('SELECT amount FROM Replenishments WHERE order_id = ?', (order_id,)).fetchone()

    def select_repl_user_amount(self, order_id):
        return self.cursor.execute('SELECT user_id, amount FROM Replenishments WHERE order_id = ?', (order_id,)).fetchone()

    def select_repl_orders(self):
        return self.cursor.execute('SELECT order_id, date FROM Replenishments').fetchall()

    def insert_repl_order(self, order_id, amount, user_id):
        self.cursor.execute('INSERT INTO Replenishments VALUES(?, ?, ?, ?)', (order_id, amount, user_id, int(time())))

    def delete_repl_by_order(self, order_id):
        self.cursor.execute('DELETE FROM Replenishments WHERE order_id = ?', (order_id,))
    # </editor-fold>

    # <editor-fold desc="Addresses table">
    def select_addr_all(self):
        return self.cursor.execute('SELECT * FROM Addresses').fetchall()

    def select_addr_address(self, user_id):
        return self.cursor.execute('SELECT address FROM Addresses WHERE user_id = ?', (user_id,)).fetchone()

    def select_addr_user(self, address):
        return self.cursor.execute('SELECT user_id FROM Addresses WHERE address = ?', (address,)).fetchone()

    def insert_addr(self, user_id):
        self.cursor.execute('INSERT INTO Addresses VALUES(?, NULL)', (user_id,))

    def delete_addr_by_user(self, user_id):
        self.cursor.execute("""UPDATE Addresses SET
                                  "address" = NULL
                                WHERE user_id = ?""", (user_id,))

    def update_addr_by_user(self, user_id, address):
        self.cursor.execute("""UPDATE Addresses SET
                                  "address" = ?
                                WHERE user_id = ?""", (address, user_id))
    # </editor-fold>

    # <editor-fold desc="Spam control table">
    def select_spam_cnt(self, user_id, is_lang=True):
        field = "lang_cnt"
        if not is_lang:
            field = "repl_cnt"
        return self.cursor.execute('SELECT {} FROM Spam_control WHERE user_id = ?'.format(field), (user_id,)).fetchone()

    def insert_spam_record(self, user_id):
        self.cursor.execute('INSERT INTO Spam_control VALUES(?, 0, 0)', (user_id,))

    def update_spam_cnt(self, user_id, is_lang=True):
        field = "lang_cnt"
        if not is_lang:
            field = "repl_cnt"
        self.cursor.execute("""UPDATE Spam_control SET
                                  "{}" = "{}" + 1
                                WHERE user_id = ?""".format(field, field), (user_id,))

    def nullify_spam(self):
        self.cursor.execute("""UPDATE Spam_control SET
                                  "lang_cnt" = 0,
                                  "repl_cnt" = 0""")
    # </editor-fold>

    # <editor-fold desc="Rewards">
    def select_reward_all(self):
        return self.cursor.execute('SELECT * FROM Rewards').fetchall()

    def select_reward(self, user_id):
        return self.cursor.execute('SELECT user_id FROM Rewards WHERE user_id = ?', (user_id,)).fetchone()

    def insert_reward(self, user_id):
        self.cursor.execute('INSERT INTO Rewards VALUES(?)', (user_id,))
    # </editor-fold>

    def close(self):
        self.connection.close()
