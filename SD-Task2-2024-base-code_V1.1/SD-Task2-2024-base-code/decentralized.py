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
#source .venv/bin/activate

import grpc
import os
import socket
import store_pb2
import store_pb2_grpc
import yaml
import logging
import asyncio
import random

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):
    """
    Implementación del servicio KeyValueStore.
    """

    def __init__(self, node_id, nodes):
        """
        Inicializa el servicio KeyValueStore.
        """
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}
        self.lock = asyncio.Lock()

    async def put(self, request, context):
        """
        Método para manejar la operación put.
        """
        async with self.lock:
            self.data[request.key] = request.value
            await self.replicate(request)
        return store_pb2.PutResponse(success=True)

    async def get(self, request, context):
        """
        Método para manejar la operación get.
        """
        async with self.lock:
            value = self.data.get(request.key, "")
        return store_pb2.GetResponse(value=value, found=bool(value))

    async def replicate(self, request):
        """
        Método para replicar los datos a otros nodos.
        """
        quorum_size = 3 if request.value else 2
        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))
        for node in nodes:
            if node != self.node_id:
                try:
                    async with grpc.aio.insecure_channel(node) as channel:
                        stub = store_pb2_grpc.KeyValueStoreStub(channel)
                        await stub.put(store_pb2.PutRequest(key=request.key, value=request.value))
                except Exception as e:
                    logging.error("Error replicating to %s: %s", node, e)


class Server:
    """
    Clase para iniciar el servidor gRPC.
    """

    def __init__(self, node_id, ip, port, nodes):
        """
        Inicializa el servidor.
        """
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.nodes = nodes
        self.server = grpc.aio.server()
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStore(self.node_id, self.nodes), self.server)

    async def start(self):
        """
        Método para iniciar el servidor.
        """
        server_address = f"{self.ip}:{self.port}"
        self.server.add_insecure_port(server_address)
        await self.server.start()
        logging.info("Server started. Listening on %s", server_address)

    async def stop(self):
        """
        Método para detener el servidor.
        """
        await self.server.stop(0)

async def main():
    """
    Función principal para iniciar los servidores.
    """
    logging.basicConfig(level=logging.INFO)
    config_path = os.path.join(os.path.dirname(__file__), 'decentralized_config.yaml')
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    servers = []
    try:
        for node in config['nodes']:
            node_id = node['id']
            ip = 'localhost'
            port = node['port']
            nodes = [f"localhost:{n['port']}" for n in config['nodes'] if n != node]
            server = Server(node_id, ip, port, nodes)
            await server.start()
            servers.append(server)
            logging.info(f"Server for node {node_id} listening on localhost:{port}")

        # Esperar a que los servidores se detengan
        await asyncio.gather(*[server.server.wait_for_termination() for server in servers])

    except KeyboardInterrupt:
        logging.info("Stopping servers...")
        await asyncio.gather(*[server.stop() for server in servers])

    finally:
        logging.info("Closing all servers...")


if __name__ == '__main__':
    asyncio.run(main())


    