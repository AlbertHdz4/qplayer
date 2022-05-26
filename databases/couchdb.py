
import couchdb

class CouchDBDatabase:

    def __init__(self,username, password, host, port, database):
        self.couch = couchdb.Server(f'http://{username}:{password}@{host}:{port}/')
        self.db = self.couch[database]

    def store_run_parameters(self, run_id, variables, iterators):
        self.db.save({'run_id':run_id, 'variables':variables, 'iterators': iterators})

    def get_latest_run_id(self):
        # TODO add code to creat index if it does't exist
        # {"index": {"fields": [{"run_id":"desc"}]},"name": "run_id-json-index","type": "json"}
        mango = {"selector": {"run_id": {"$gte": 0}}, "sort": [{"run_id": "desc"}], "limit": 1}
        # print(mango)
        try:
            row = next(self.db.find(mango))
            return row['run_id']
        except StopIteration: # New database
            return 0