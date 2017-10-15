import sqlite3


class Users_db:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, isolation_level=None)
        self.cursor = self.connection.cursor()

    # Statistics table
    def select_stats(self, user_id):
        return self.cursor.execute('SELECT * FROM Statistics WHERE user_id = ?', (user_id,)).fetchone()

    def select_is_eng(self, user_id):
        return self.cursor.execute('SELECT is_eng FROM Statistics WHERE user_id = ?', (user_id,)).fetchone()[0]

    def is_exist_stats(self, user_id):
        return self.cursor.\
            execute('SELECT EXISTS(SELECT user_id FROM Statistics WHERE user_id = ?)', (user_id,)).fetchone()[0]

    def insert_stats(self, data):
        self.cursor.execute('INSERT INTO Statistics VALUES(?, ?, ?, ?, ?)', data)

    def update_stats_profit(self, user_id, balance, profit):
        self.cursor.execute("""UPDATE Statistics SET 
                                  balance = balance + ?,
                                  profit = profit + ?
                                WHERE user_id = ?""", (balance, profit, user_id))

    def update_stats_invested(self, user_id, invested):
        self.cursor.execute("""UPDATE Statistics SET 
                                  invested = invested + ?
                                WHERE user_id = ?""", (invested, user_id))

    def update_stats_lang(self, user_id, is_eng):
        self.cursor.execute("""UPDATE Statistics SET 
                                  is_eng = ?
                                WHERE user_id = ?""", (is_eng, user_id))

    # Ref_program table
    def select_ref_all(self, user_id):
        return self.cursor.execute('SELECT * FROM Ref_program WHERE user_id = ?', (user_id,)).fetchone()

    def select_ref_inviter(self, user_id):
        return self.cursor.execute('SELECT inviter FROM Ref_program WHERE user_id = ?', (user_id,)).fetchone()[0]

    def insert_ref(self, user_id):
        self.cursor.execute('INSERT INTO Ref_program VALUES(?, NULL, NULL, NULL, NULL)', (user_id,))

    def update_ref_inviter(self, user_id, inviter):
        self.cursor.execute("""UPDATE Ref_program SET 
                                  inviter = ?
                                WHERE user_id = ?""", (inviter, user_id))

    def update_ref_line(self, user_id, line_number, line_value):
        line_name = str(line_number) + "_line"
        self.cursor.execute("""UPDATE Ref_program SET 
                                  {} = IFNULL({}, 0) +  ?
                                WHERE user_id = ?""".format(line_name, line_name), (line_value, user_id))

    # Salts table
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

    # Requisites table
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
                                  {} = ?
                                WHERE user_id = ?""".format(requisite_name), (requisite, user_id))

    def close(self):
        self.connection.close()


if __name__ == "__main__":
    pass
