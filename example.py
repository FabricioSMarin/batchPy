from queue_server import rqs
from redis import Redis

host = "164.54.113.75"
port = "6666"
# conf = "/home/beams0/MARINF/conda/batchPy/redis.conf"
r = Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)  
r.ping()
r.get("settings")

params = {}
params["generator"]= "scan_record"
# params["generator"]= "profile_move"
params["geometry"] = "2D"
params["type"] = "fly"
params["detectors"] = [None]
params["trajectory"] = "raster"
params["dwell"] = 20 #ms
params["notes"] = "test params "
params["x_width"] = 1
params["x_center"] = 0
params["x_step"] = 0.01
params["y_width"] = 1
params["y_center"] = 0
params["y_step"] = 0.01
params["x_width"] = 1

scan_id, eta, msg = add_to_q(params)

#redis keys: "settings", "commands", "queue"
# settings: {param: pv_name}
# commands: {function_name: args}
# queue: {scan_id: {params: val}}