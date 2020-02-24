# prometheus custom exporter

Custom exporter plugin written in python3.

Exporter will fetch and expose the stats field of the axapis mentioned in the prometheus.yml config file.

Prometheus server will call the exporter as per the time interval specified in config file in order to get the stats.

Prometheus test utility helps to automate the process of posting stats data on the axapi endpoints provided in api file.
Uyility also generates prometheus.yml config file at runtime and launch the exporter mentioned above.
