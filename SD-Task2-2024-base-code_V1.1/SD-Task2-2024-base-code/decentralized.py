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
#ejecutar test con varios threads a la vez, mas rapido: pytest -n 4 eval/decentralized_system_tests.py
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

# Definir el servicio KeyValueStore
class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, node_id, nodes):
        # Inicializar el servicio con un ID de nodo y una lista de nodos
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}  # Datos almacenados en el nodo
        self.lock = asyncio.Lock()  # Lock para garantizar la exclusión mutua en la modificación de datos

    async def put(self, request, context):
        async with self.lock:  # Adquirir el lock
            # Almacenar el valor asociado a la clave en los datos del nodo
            self.data[request.key] = request.value
            await self.replicate(request)  # Replicar los datos a otros nodos
        return store_pb2.PutResponse(success=True)  # Enviar una respuesta de éxito al cliente

    async def get(self, request, context):
        async with self.lock:  # Adquirir el lock
            # Obtener el valor asociado a la clave desde los datos del nodo
            value = self.data.get(request.key, "")
        return store_pb2.GetResponse(value=value, found=bool(value))  # Enviar el valor encontrado al cliente

    async def replicate(self, request):
        quorum_size = 3 if request.value else 2  # Determinar el tamaño del quórum
        # Seleccionar aleatoriamente nodos para replicar los datos
        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))
        for node in nodes:
            if node != self.node_id:
                try:
                    async with grpc.aio.insecure_channel(node) as channel:
                        stub = store_pb2_grpc.KeyValueStoreStub(channel)
                        # Llamar al método put en el nodo remoto para replicar los datos
                        await stub.put(store_pb2.PutRequest(key=request.key, value=request.value))
                except grpc.RpcError as e:
                    logging.error("Error replicating to %s: %s", node, e)

# Clase para iniciar el servidor gRPC
class Server:
    def __init__(self, node_id, ip, port, nodes):
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.nodes = nodes
        # Inicializar el servidor gRPC
        self.server = grpc.aio.server(options=[('grpc.max_send_message_length', -1), ('grpc.max_receive_message_length', -1)])
        # Agregar el servicio KeyValueStore al servidor
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStore(self.node_id, self.nodes), self.server)

    async def start(self):
        # Iniciar el servidor gRPC en la dirección y puerto especificados
        server_address = f"{self.ip}:{self.port}"
        self.server.add_insecure_port(server_address)
        await self.server.start()
        logging.info("Server started. Listening on %s", server_address)

    async def stop(self):
        # Detener el servidor gRPC
        await self.server.stop(0)

# Función principal para iniciar los servidores
async def main():
    logging.basicConfig(level=logging.INFO)
    config_path = os.path.join(os.path.dirname(__file__), 'decentralized_config.yaml')
    # Cargar la configuración desde el archivo YAML
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    servers = []
    try:
        # Iniciar un servidor para cada nodo en la configuración
        for node in config['nodes']:
            node_id = node['id']
            ip = 'localhost'
            port = node['port']
            # Construir una lista de nodos excluyendo el nodo actual
            nodes = [f"localhost:{n['port']}" for n in config['nodes'] if n != node]
            server = Server(node_id, ip, port, nodes)
            await server.start()
            servers.append(server)
            logging.info(f"Server for node {node_id} listening on localhost:{port}")

        # Esperar a que todos los servidores se detengan
        await asyncio.gather(*[server.server.wait_for_termination() for server in servers])
    except KeyboardInterrupt:
        logging.info("Stopping servers...")
        await asyncio.gather(*[server.stop() for server in servers])
    finally:
        logging.info("Closing all servers...")

# Ejecutar la función principal si este archivo se ejecuta como un script
if __name__ == '__main__':
    asyncio.run(main())