import sqlite3


class Users_db:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, isolation_level=None)
        self.cursor = self.connection.cursor()

    # Statistics table
    def select_stats(self, user_id):
        return self.cursor.execute('SELECT * FROM Statistics WHERE user_id = ?', (user_id,)).fetchone()

    def is_exist_stats(self, user_id):
        return self.cursor.\
            execute('SELECT EXISTS(SELECT user_id FROM Statistics WHERE user_id = ?)', (user_id,)).fetchone()[0]

    def insert_stats(self, data):
        self.cursor.execute('INSERT INTO Statistics VALUES(?, ?, ?, ?, ?)', data)

    def update_stats_profit(self, data):
        self.cursor.execute("""UPDATE Statistics SET 
                                  balance = balance + ?,
                                  profit = profit + ?
                                WHERE user_id = ?""", (data[1], data[2], data[0]))

    def update_stats_invested(self, data):
        self.cursor.execute("""UPDATE Statistics SET 
                                  invested = invested + ?
                                WHERE user_id = ?""", (data[1], data[0]))

    def update_stats_lang(self, data):
        self.cursor.execute("""UPDATE Statistics SET 
                                  is_eng = ?
                                WHERE user_id = ?""", (data[1], data[0]))

    # Ref_program table
    def select_ref_all(self, user_id):
        return self.cursor.execute('SELECT * FROM Ref_program WHERE user_id = ?', (user_id,)).fetchone()

    def select_ref_inviter(self, user_id):
        return self.cursor.execute('SELECT inviter FROM Ref_program WHERE user_id = ?', (user_id,)).fetchone()[0]

    def insert_ref(self, user_id):
        self.cursor.execute('INSERT INTO Ref_program VALUES(?, NULL, NULL, NULL, NULL)', (user_id,))

    def update_ref_inviter(self, data):
        self.cursor.execute("""UPDATE Ref_program SET 
                                  inviter = ?,
                                WHERE user_id = ?""", (data[1], data[0]))

    def update_ref_line(self, data, line_number):
        line_name = str(line_number) + "_line"
        self.cursor.execute("""UPDATE Ref_program SET 
                                  {} = ?,
                                WHERE user_id = ?""".format(line_name), (data[1], data[0]))

    def close(self):
        self.connection.close()

