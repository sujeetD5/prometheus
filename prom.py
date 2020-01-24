from flask import Response, Flask
import prometheus_client
from prometheus_client import Gauge
import requests, json
import urllib3


app = Flask(__name__)

_INF = float("inf")

def getauth():
   payload = {'Credentials': {'username': 'admin', 'password': 'devops123'}}
   auth = json.loads(
       requests.post("https://10.43.12.122/axapi/v3/auth", json=payload, verify=False).content.decode('UTF-8'))
   return 'A10 ' + auth['authresponse']['signature']


@app.route("/")
def hello():
   return "Please provide /metrics/service-name!"


aflow_metrics = Gauge(
   'aflow',
   'aflow',
   labelnames=(["try_to_resume_conn", 'retry_resume_conn']),
)

@app.route("/metrics/aflow")
def requests_aflow():
   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
   token = getauth()
   endpoint = "http://10.43.12.122/axapi/v3/slb/aflow/stats"
   headers = {'content-type': 'application/json', 'Authorization': token}
   print("endpoint = ", endpoint)
   response = json.loads(requests.get(endpoint, headers=headers, verify=False).content.decode('UTF-8'))
   print("response = ", response)
   stats = response['aflow']['stats']
   res = []

   data = [stats["try_to_resume_conn"], stats['retry_resume_conn']]
   aflow_metrics.labels(*data)
   res.append(prometheus_client.generate_latest(aflow_metrics))
   return Response(res, mimetype="text/plain")



# @app.route("/metrics/service-group")
# def requests_service_group():
#     urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#     endpoint = "http://10.43.12.122/axapi/v3/slb/service-group"
#     token = getauth()
#     headers = {'content-type': 'application/json', 'Authorization': token}
#     response = json.loads(requests.get(endpoint, headers=headers, verify=False).content.decode('UTF-8'))
#     token = getauth()
#     res = []
#     print(response["service-group-list"])
#     for data in response["service-group-list"]:
#         name = data.get("name")
#         headers = {'content-type': 'application/json', 'Authorization': token}
#         print("endpoint = ", endpoint)
#         response = json.loads(requests.get(endpoint+"/"+name+"/stats", headers=headers, verify=False).content.decode('UTF-8'))
#         print("response = ", response)
#         stats = response['service-group']['stats']
#
#         data = {name: {"server_selection_fail_reset": stats["server_selection_fail_reset"],
#                            "service_peak_conn": stats['service_peak_conn']}}
#         service_group.labels(data)
#
#         res.append(prometheus_client.generate_latest(service_group))
#     return Response(res, mimetype="text/plain")

# service_group = Gauge(
#     'sgroup_metrics',
#     'service-group',
#     labelnames=(["sgroup"]),
# )

service_group = dict()

@app.route("/metrics/service-group/<sg_name>")
def service_group_func(sg_name):
   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
   token = getauth()
   endpoint = "http://10.43.12.122/axapi/v3/slb/service-group"
   headers = {'content-type': 'application/json', 'Authorization': token}
   print("endpoint = ", endpoint)
   response = json.loads(requests.get(endpoint+"/"+sg_name+"/stats", headers=headers, verify=False).content.decode('UTF-8'))
   print("response = ", response)
   try:
       stats = response['service-group']['stats']
   except:
       return sg_name+" not found"
   print(service_group)
   if sg_name not in service_group:
       service_group[sg_name] = Gauge(
           sg_name,
           'service-group',
           labelnames=(["sgroup"]),
       )
   data = {sg_name: {"server_selection_fail_reset": stats["server_selection_fail_reset"],
                     "service_peak_conn": stats['service_peak_conn']}}
   print(service_group)
   service_group[sg_name].labels(data)
   res = [prometheus_client.generate_latest(service_group[sg_name])]
   return Response(res, mimetype="text/plain")

vserver = dict()


@app.route("/metrics/virtual-server/<vs_name>/port/<port_protocol>")
def virtual_server(vs_name, port_protocol):
   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
   token = getauth()
   endpoint = "http://10.43.12.122/axapi/v3/slb/virtual-server"
   headers = {'content-type': 'application/json', 'Authorization': token}
   print("endpoint = ", endpoint)
   response = json.loads(
       requests.get(endpoint + "/" + vs_name + "/port/" + port_protocol + "/stats", headers=headers, verify=False).content.decode('UTF-8'))
   print("response = ", response)
   try:
       stats = response['port']['stats']
   except:
       return vs_name + " not found"
   print(vserver)
   if vs_name not in vserver:
       vserver[vs_name] = Gauge(
           vs_name,
           'virtual-server',
           labelnames=(["vsgroup"]),
       )
   data = {vs_name: {"total_rev_pkts": stats["total_rev_pkts"],
                     "total_rev_pkts_out": stats['total_rev_pkts_out']}}
   print(service_group)
   vserver[vs_name].labels(data)
   res = [prometheus_client.generate_latest(vserver[vs_name])]
   return Response(res, mimetype="text/plain")

if __name__ == '__main__':
   app.run(debug=True, port=7070)



