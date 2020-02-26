from flask import Response, Flask, request
import prometheus_client
from prometheus_client import Gauge
import requests, json
import urllib3
from prometheus_client.registry import CollectorRegistry

app = Flask(__name__)

_INF = float("inf")

def getauth(host):
   payload = {'Credentials': {'username': 'admin', 'password': 'a10'}}
   auth = json.loads(
       requests.post("https://{host}/axapi/v3/auth".format(host=host), json=payload, verify=False).content.decode('UTF-8'))
   return 'A10 ' + auth['authresponse']['signature']


@app.route("/")
def hello():
   return "Please provide /metrics/service-name!"

endpoint_labels = dict()

@app.route("/metrics")
def generic_exporter():
   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
   host_ip = request.args["host_ip"]
   api_endpoint = request.args["api_endpoint"]
   api_name = request.args["api_name"]
   token = getauth(host_ip)

   endpoint = "http://{host_ip}/axapi/v3".format(host_ip=host_ip)
   headers = {'content-type': 'application/json', 'Authorization': token}
   # print("endpoint = ", endpoint)
   print(endpoint + api_endpoint + "/stats")
   response = json.loads(
       requests.get(endpoint + api_endpoint + "/stats", headers=headers, verify=False).content.decode('UTF-8'))
   # print("response = ", response)
   try:
       key = list(response.keys())[0]
       event = response.get(key)
       stats = event.get("stats", {})
   except Exception as e:
       print(e)
       return api_endpoint + " have something missing."

   print("name = ", api_name)

   if api_name not in endpoint_labels:
       dictmetrics= dict()
       for key in stats:
           dictmetrics[key] = Gauge(key, "api-" + api_name +"key-" + key, labelnames=(["data"]),)
           data = {api_name: key}
           dictmetrics[key].labels(data).set(stats[key])
       endpoint_labels[api_name] = dictmetrics

   #data = {metrics_name: stats}
   #endpoint_labels[metrics_name].labels(data).set(11)
   res=[]
   for name in endpoint_labels[api_name]:
       res.append(prometheus_client.generate_latest(endpoint_labels[api_name][name]))
   return Response(res, mimetype="text/plain")


if __name__ == '__main__':
   app.run(debug=True, port=7070)