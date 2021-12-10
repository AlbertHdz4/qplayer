from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from database import Database

class InfluxDB2(Database):

    def __init__(self, url, token, org, bucket):
        self.bucket = bucket
        self.org = org
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def store_run_parameters(self, run_id, parameters):

        parameters_str = "experiment-run "
        for k in parameters:
            parameters_str += "%s=%s,"%(k, parameters[k])

        parameters_str += "_run_id=%d"%run_id

        self.write_api.write(self.bucket, self.org, parameters_str)