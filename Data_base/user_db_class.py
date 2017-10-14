import sqlite3


class Stats_db:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, isolation_level=None)
        self.cursor = self.connection.cursor()

    def select_single(self, user_id):
        return self.cursor.execute('SELECT * FROM Statistics WHERE user_id = {}'.format(user_id)).fetchone()

    def insert_single(self, data):
        self.cursor.execute("""INSERT INTO Statistics VALUES({}, {}, {}, {})""".format(*data))

    def update_single(self, data):
        self.cursor.execute("""UPDATE Statistics SET 
                                  balance = {balance},
                                  invested = {invested},
                                  profit = {profit}
                                WHERE user_id = {user_id}""".format(balance=data[1], invested=data[2],
                                                                    profit=data[3], user_id=data[0]))

    def close(self):
        self.connection.close()
