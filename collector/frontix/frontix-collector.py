

# This script expects the module cx_Oracle to be installed
# By default extra modules cannot/should not installed in Splunk
# So make sure to run this module from a shell script that first
# imports a virtual environment that has the mocule installed
#
# This means that no direct interaction with the Splunk
# libraries will be possible


import cx_Oracle
import pickle
from SQLParameters import SQLParameters
import sys
import os
from importlib import import_module
import re
import logging
import glob


logger = logging.getLogger("findhost-frontix-collector")
#handler = logging.StreamHandler(stream=sys.stderr)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


QUERY_LIMIT = int(os.environ.get("QUERY_LIMIT", 10000000))
DEFAULT_POSTPROCESSOR = "ppcsv"
FILTER = None


def read_args():
    """
    Expected commandline:
    python frontix-modinput-connector.py  sql_dir  dump_dir  [filter]

    Returns:
    params = {
        "arg1": "value1",
        "arg2": "value2",
        etc
    }
    """

    params = {"filter": FILTER}

    if len(sys.argv) <= 2:
        return params

    params["sql_dir"] = sys.argv[1]
    params["dump_dir"] = sys.argv[2]

    if len(sys.argv) >= 4:
        params["filter"] = sys.argv[3]

    logger.debug("params = {}".format(params))

    return params


def execute_oracle_query(hostname, port, service, user, pwd, query):
    """
    Connect to Oracle and execute the query
    """
    conn = None
    columns = None
    c = None

    try:
        logger.debug("-- checkpoint A1 --")
        dsn_tns = cx_Oracle.makedsn(hostname, port, service_name=service)
        logger.debug("-- checkpoint A2 --")
        conn = cx_Oracle.connect(user=user, password=pwd, dsn=dsn_tns)
        logger.debug("-- checkpoint A3 --")
        c = conn.cursor()
        logger.debug("-- checkpoint A4 --")
        c.execute(query)
        logger.debug("-- checkpoint A5 --")
        columns = [x[0] for x in c.description]
        logger.debug("-- checkpoint A6 --")

    except Exception as e:
        logger.critical("--- ERROR OCCURRED EXECUTING THE SQL QUERY ---")
        logger.critical(str(e))

    logger.debug("-- checkpoint A7 --")

    return conn, columns, c


def get_queries(query_folder, query_filter=None):
    """
    Read the query folder and return:
    {
        "filename": "query"
    }
    """
    logger.debug("look for query files in: {}".format(query_folder))
    queries = {}
    files = [f for f in glob.glob(os.path.join(
        query_folder, "*.sql"), recursive=False)]

    for f in files:
        # skip if the query is no match
        if query_filter and query_filter not in f:
            logger.info("filter applied - skip query file {}".format(f))
            continue
        sql_file = open(f, "r").read()
        sql_file = sql_file.replace("\n", " ")
        sql_file = sql_file.replace("\t", " ")
        queries[f] = sql_file
        logger.info("new query file found: {}".format(f))
    return queries


class ConnectionDetails:
    """Stores a Frontix connection, we may have MES or OBE Frontix for example
    """

    def __init__(self, *args, **kwargs):
        self.hostname = kwargs.get("hostname", None)
        self.port = kwargs.get("port", None)
        self.service = kwargs.get("service", None)
        self.sid = kwargs.get("sid", None)
        self.user = kwargs.get("user", None)
        self.pwd = kwargs.get("pwd", None)

        self._conn = None

    @property
    def conn(self):
        """Returns the Oracle connection handle, if it doesn not
        exist yet then create it first
        """
        if not self._conn:
            self._conn = self._connect()
        return self._conn

    def close(self):
        """Closes the connection"""
        if self._conn:
            self._conn.close()

    def _connect(self):
        """Connects to the oracle DB and return the connection handle
        """
        conn = None
        try:
            if self.service:
                dsn_tns = cx_Oracle.makedsn(
                    self.hostname, self.port, service_name=self.service)
            else:
                dsn_tns = cx_Oracle.makedsn(self.hostname, self.port, self.sid)

            conn = cx_Oracle.connect(
                user=self.user, password=self.pwd, dsn=dsn_tns)

            logger.debug("Connected to DB:{}, user:{}".format(
                self.hostname, self.user))
        except Exception as e:
            logger.critical("--- ERROR OCCURRED EXECUTING THE SQL QUERY ---")
            logger.critical(str(e))

        return conn

    def query(self, query):
        """Runs an SQL query and returns a tuple of
        columns, cursor
        """
        conn = self.conn

        columns = None
        c = None

        try:
            c = conn.cursor()
            c.execute(query)
            columns = [x[0] for x in c.description]

        except Exception as e:
            logger.critical("--- ERROR OCCURRED EXECUTING THE SQL QUERY ---")
            logger.critical(str(e))

        return columns, c


def main():

    params = read_args()

    # MES FRONTIX CONNECTION DETAILS
    mes_frontix_conn = ConnectionDetails(
        hostname=os.environ.get("FTX_HOSTNAME", None),
        port=os.environ.get("FTX_PORT", None),
        service=os.environ.get("FTX_SERVICE", None),
        user=os.environ.get("FTX_USER", None),
        pwd=os.environ.get("FTX_PWD", None)
    )

    # ORANGE FRONTIX CONNECTION DETAILS
    obe_frontix_conn = ConnectionDetails(
        hostname=os.environ.get("FTX_OBE_HOSTNAME", None),
        port=os.environ.get("FTX_OBE_PORT", None),
        sid=os.environ.get("FTX_OBE_SID", None),
        user=os.environ.get("FTX_OBE_USER", None),
        pwd=os.environ.get("FTX_OBE_PWD", None)
    )

    # hostname = os.environ.get("FTX_HOSTNAME", None)
    # port = os.environ.get("FTX_PORT", None)
    # service = os.environ.get("FTX_SERVICE", None)
    # user = os.environ.get("FTX_USER", None)
    # pwd = os.environ.get("FTX_PWD", None)

    postprocessor = os.environ.get("FTX_POSTPROCESSOR", None)

    query_limit = QUERY_LIMIT

    # import the postprocessor module
    try:
        # if postprocessor and os.path.exists("postprocessors/{}.py".format(postprocessor)):
        if postprocessor:
            ext = import_module("postprocessors.{}".format(postprocessor))
            logger.debug("using postprocessor: {}".format(postprocessor))
        else:
            ext = import_module(
                "postprocessors.{}".format(DEFAULT_POSTPROCESSOR))
            logger.debug("using default postprocessor: {}".format(
                DEFAULT_POSTPROCESSOR))
    except:
        ext = None
        logger.warn("error loading postprocessor")

    queries = get_queries(params["sql_dir"], params["filter"])

    for q in queries:

        query = queries[q]
        logger.info("start executing query {}: {}".format(q, query))

        m = re.match(".* where .*", query, re.I)
        if m:
            if "ORDER BY" in query:
                query = query.replace(
                    "ORDER BY", "AND ROWNUM <= {} ORDER BY".format(query_limit))
            else:
                query = query + " AND ROWNUM <= {}".format(query_limit)
        else:
            query = query + " WHERE ROWNUM <= {}".format(query_limit)

        logger.debug("SQL query [{}] = {}".format(q, query))

        # if the query filename contains <filename>.obe.sql then use the OBE FTX params
        # otherwise use MES FTX params
        if q.endswith(".obe.sql"):
            conn = obe_frontix_conn
        else:
            conn = mes_frontix_conn

        logger.info(
            "connect to SQL using these parameters: {}".format(conn.hostname))
        columns, rows = conn.query(query)

        # connection, columns, rows = execute_oracle_query(
        #     hostname, port, service, user, pwd, query)

        #print("connection: {}".format(connection))
        logger.debug("columns: {}".format(columns))
        #print("rows: {}".format(rows))

        OUT = open(os.path.join(
            params["dump_dir"], (os.path.split(q)[-1]).replace(".sql", ".csv")), "w")

        rowcount = 0
        for row in rows:
            # print(row)

            # execute the post_processor
            # by default this just returns a JSON with { row: column }
            if rowcount == 0:
                HEADER = True
            else:
                HEADER = False
            data = ext.post_processor(columns, row, header=HEADER)
            # print(data)
            OUT.write(data)
            OUT.write("\n")

            # don't return more rows than the built-in threshold
            rowcount += 1
            if QUERY_LIMIT and rowcount >= QUERY_LIMIT:
                break

        OUT.close()

        logger.info("found {} records".format(rowcount))

        # if the oracle connection is still open then close it now
        conn.close()

        # if connection:
        #     connection.close()


if __name__ == '__main__':
    main()
