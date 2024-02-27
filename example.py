from queu_server import rqs

batch = rqs()
host = batch.settings.host
port = batch.settings.port
conf = batch.settings.conf

batch.start_server(host=host,port=port,conf=conf)
batch.connect_server(host=host,port=port)

batch.r.ping()

batch.
