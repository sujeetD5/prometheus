import json
import sys
import prometheus_client
import requests
import urllib3
from flask import Response, Flask, request
from prometheus_client import Gauge
import logging

UNDERSCORE = "_"
SLASH = "/"
HYPHEN = "-"
PLUS = "+"

dictmetrics = dict()

app = Flask(__name__)
global auth_signature

_INF = float("inf")


def set_logger(log_file, log_level):
    try:
        logging.basicConfig(
            filename=log_file,
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%FT%T%z',
            level={
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARN': logging.WARN,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL,
            }[log_level.upper()])
    except Exception as e:
        print('Error while setting logger config::%s', e)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger('a10_prometheus_exporter_logger')
    return logger

def getauth(host):
    global auth_signature
    if len(auth_signature) != 0:
        return auth_signature

    with open('config.json') as f:
        data = json.load(f)
        data = data["hosts"]
    if host not in data:
        print("Host credentials not found in creds config")
        return ''
    else:
        uname = data[host]['username']
        pwd = data[host]['password']

        payload = {'Credentials': {'username': uname, 'password': pwd}}
        auth = json.loads(
            requests.post("https://{host}/axapi/v3/auth".format(host=host), json=payload, verify=False).content.decode(
                'UTF-8'))
        auth_signature = 'A10 ' + auth['authresponse']['signature']
        return auth_signature


@app.route("/")
def default():
    return "Please provide /metrics/service-name!"

def getapilist():
    file1 = open('apis.txt', 'r')
    Lines = file1.readlines()
    list = []
    for line in Lines:
        line = line.strip()
        list.append(line)
    return list

def packPrometheusGaugesForMetircs(labelName , stats):
    print(stats)
    for key in stats:
        org_key = key
        if HYPHEN in key:
            key = key.replace(HYPHEN, UNDERSCORE)
        if key not in dictmetrics:
            dictmetrics[key] = Gauge(key,"Custome help String",labelnames=(["data"]), )
            # Gauge will be created with unique identifier as combination of ("api_name_key_name")
        dictmetrics[key].labels(labelName).set(stats[org_key])

    return

def getLabenNameFromA10URL(str_a10_url, api_list_str):

    truncate_start_index = len(api_list_str)-len('stats')
    truncate_end_index = len(str_a10_url)-len('/stats')

    print("str_a10_url: "+str_a10_url)
    print("api_list_str: "+api_list_str)

    labelName = str_a10_url[truncate_start_index:truncate_end_index]
    labelName = labelName.replace(SLASH, UNDERSCORE)
    labelName = labelName.replace(HYPHEN, UNDERSCORE)
    labelName = labelName.replace(PLUS, UNDERSCORE)

    print("Modified lableName:"+labelName)
    return labelName

def parseResponseForAllStats(response, api_list_str):
    print("checkpoint1")
    if response == None:
        return
    print("checkpoint2")
    if type(response) is list:
        print("checkpoint3")
        for item in response:
            parseResponseForAllStats(item, api_list_str)

    if type(response) is dict:
        print("checkpoint4")
        #check for its stat first and pack for prometheus
        for key in response.keys():
            if 'stats' == key:
                labelName = getLabenNameFromA10URL(response['a10-url'], api_list_str)
                packPrometheusGaugesForMetircs(labelName, response['stats'])
            else:
                if type(response[key]) is list:
                    parseResponseForAllStats(response[key], api_list_str)
    print("checkpoint5")
    return


@app.route("/metrics")
def generic_exporter():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print(request.args)
    host_ip = "10.65.22.154"
    api_list = getapilist()
    print(api_list)

    token = getauth(host_ip)
    print("token :"+token)
    if token == '':
        print("Username, password does not match, token can not be empty, exiting")
        sys.exit()

    endpoint = "http://{host_ip}{stats_endpoint}".format(host_ip=host_ip, stats_endpoint=api_list[0])
    headers = {'content-type': 'application/json', 'Authorization': token}
    print("endpoint = ", endpoint)
    response = json.loads(
        requests.get(endpoint, headers=headers, verify=False).content.decode('UTF-8'))

    parseResponseForAllStats(response, api_list[0])

    res = []
    for name in dictmetrics:
        res.append(prometheus_client.generate_latest(dictmetrics[name]))

    return Response(res, mimetype="text/plain")


def main():
    app.run(debug=True, port=7070)

if __name__ == '__main__':
    global auth_signature
    auth_signature = ''
    with open('config.json') as f:
        data = json.load(f)
        data = data["log"]
    try:
        logger = set_logger(data["log_file"], data["log_level"])
    except Exception as e:
        print("Config file is not correct")
        print(e)
        sys.exit()

    logger.info("Starting exporter")
    main()
