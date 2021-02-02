
# mysqlclient documentation https://mysqlclient.readthedocs.io/
from MySQLdb import _mysql


class Database:
    def __init__(self, db_config):
        self.db = _mysql.connect(db_config['dbhost'], db_config['dbuser'], db_config['dbpasswd'], db_config['dbname'])
