import grpc
import sys
import os
import socket

# Agregar la ruta al directorio proto al Python PATH
proto_dir = os.path.join(os.path.dirname(__file__), 'proto')
sys.path.append(proto_dir)
#python -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. ./store.proto
#python .\eval\decentralized_system_tests.py
#python .\decentralized.py
import store_pb2
import store_pb2_grpc
import yaml 
import logging
from concurrent import futures
import time
import random
import threading

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}
        self.lock = threading.Lock()

    def put(self, request, context):
        with self.lock:
            self.data[request.key] = request.value
        self.replicate(request)
        return store_pb2.Response(success=True)

    def get(self, request, context):
        with self.lock:
            value = self.data.get(request.key, "")
        return store_pb2.GetResponse(value=value)

    def slowDown(self, request, context):
        time.sleep(request.seconds)
        return store_pb2.SlowDownResponse(success=True)

    def restore(self, request, context):
        return store_pb2.RestoreResponse(success=True)

    def replicate(self, request):
        quorum_size = 3 if request.value else 2
        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))
        for node in nodes:
            if node != self.node_id:
                channel = grpc.insecure_channel(node)
                stub = store_pb2_grpc.KeyValueStoreStub(channel)
                stub.put(store_pb2.PutRequest(key=request.key, value=request.value))

def serve(node_id, nodes, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    store_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStore(node_id, nodes), server)
    server_address = f"localhost:{port}"
    server.add_insecure_port(server_address)
    server.start()
    logging.info("Server started. Listening on %s", server_address)
    
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)  # O cualquier otro método para mantener el proceso activo
    except KeyboardInterrupt:
        server.stop(0)

def main():
    logging.basicConfig(level=logging.INFO)

    # Construir la ruta al archivo YAML
    config_path = os.path.join(os.path.dirname(__file__), 'decentralized_config.yaml')

    # Abrir el archivo YAML
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    node_id = f"{config['nodes'][0]['ip']}:{config['nodes'][0]['port']}"
    nodes = [f"{node['ip']}:{node['port']}" for node in config['nodes']]

    # Obtener el puerto del primer nodo para que el servidor escuche
    port = 50051  # Puerto por defecto

    serve(node_id, nodes, port)

if __name__ == '__main__':
    main()