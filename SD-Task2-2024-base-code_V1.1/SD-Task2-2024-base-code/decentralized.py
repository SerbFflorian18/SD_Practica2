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

#ejecutar test con varios threads a la vez, mas rapido: python -m unittest eval/decentralized_system_tests.py

#al detectar el primer erro para: python -m unittest -f eval/decentralized_system_tests.py

# 

import signal

import grpc

import socket

import store_pb2

import store_pb2_grpc

import yaml

import logging

import asyncio
import json
import random

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}
        self.lock = asyncio.Lock()  # Lock para operaciones de escritura y lectura

    async def put(self, request, context):
        async with self.lock:
            self.data[request.key] = request.value  # Modificar datos de manera segura
            await self.persist_data()  # Guardar datos en disco
            await self.propagate_put(request)
        return store_pb2.PutResponse(success=True)

    async def get(self, request, context):
        async with self.lock:
            value = self.data.get(request.key, "")
        return store_pb2.GetResponse(value=value, found=bool(value))

    async def persist_data(self):
        with open('data.json', 'w') as file:
            json.dump(self.data, file)

    async def recover_data(self):
        try:
            with open('data.json', 'r') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            logging.warning("Data file not found. Starting with empty data.")

    async def replicate(self, request):
        quorum_size = 3 if request.value else 2
        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))
        for node in nodes:
            if node != self.node_id:
                await self.propagate_put(request)

    async def propagate_put(self, request):
        try:
            # Determinar el tamaño del quórum basado en la cantidad de nodos disponibles
            quorum_size = max(2, len(self.nodes) // 2 + 1)
            
            # Seleccionar nodos aleatorios para solicitar votos
            nodes = random.sample(self.nodes, quorum_size)
            
            # Enviar solicitudes de voto a los nodos seleccionados
            votes = await asyncio.gather(*[self.request_vote(node, request) for node in nodes])
            
            # Contar los votos recibidos (incluido el voto propio)
            num_votes = sum(1 for vote in votes if vote.vote == self.node_id) + 1
            
            # Verificar si se ha alcanzado el quórum necesario
            if num_votes >= quorum_size:
                await self.commit_to_node(self.node_id, request)
        except Exception as e:
            logging.error("Error in propagate_put: %s", e)

    async def request_vote(self, node, request):
        return await self.ask_vote(request, None)

    async def commit_to_node(self, node, request):
        async with grpc.aio.insecure_channel(node) as channel:
            stub = store_pb2_grpc.KeyValueStoreStub(channel)
            await stub.do_commit(store_pb2.CommitRequest(key=request.key, value=request.value))

    async def propagate_get(self, request):
        try:
            values = await asyncio.gather(*[self.request_value(node, request) for node in self.nodes if node != self.node_id])
            values = [value.value for value in values if value.value]
            if values:
                return values[0]
            else:
                return None
        except Exception as e:
            logging.error("Error in propagate_get: %s", e)
            return None

    async def request_value(self, node, request):
        async with grpc.aio.insecure_channel(node) as channel:
            stub = store_pb2_grpc.KeyValueStoreStub(channel)
            return await stub.get(store_pb2.GetRequest(key=request.key))

    async def ask_vote(self, request, context):
        return store_pb2.VoteResponse(vote=self.node_id)
    
    async def slowDown(self, request, context):
        try:
            # Agregar un retraso a las operaciones
            delay = request.delay
            await asyncio.sleep(delay)
            return store_pb2.SlowDownResponse(success=True)
        except asyncio.CancelledError:
            logging.info("SlowDown operation cancelled")
            return store_pb2.SlowDownResponse(success=False)
        except Exception as e:
            logging.error("Error in slowDown: %s", e)
            return store_pb2.SlowDownResponse(success=False)
    
async def start_servers():
    logging.basicConfig(level=logging.INFO)
    config_path = os.path.join(os.path.dirname(__file__), 'decentralized_config.yaml')
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    servers = []
    try:
        for node in config['nodes']:
            node_id = node['id']
            ip = node['ip']
            port = node['port']
            nodes = [f"{n['ip']}:{n['port']}" for n in config['nodes'] if n != node and 'ip' in n and 'port' in n]
            service = KeyValueStore(node_id, nodes)
            await service.recover_data()  # Recuperar datos del disco al iniciar
            server = Server(service, ip, port)
            server_address = f"{ip}:{port}"
            server.server.add_insecure_port(server_address)
            await server.server.start()
            servers.append(server)
            logging.info(f"Server for node {node_id} listening on {server_address}")
        await asyncio.gather(*[server.server.wait_for_termination() for server in servers])
    except KeyboardInterrupt:
        logging.info("Stopping servers...")
        await asyncio.gather(*[server.stop() for server in servers])
    finally:
        logging.info("Closing all servers...")

class Server:
    def __init__(self, service, ip, port):
        self.service = service
        self.ip = ip
        self.port = port
        self.server = grpc.aio.server(options=[('grpc.max_send_message_length', -1), ('grpc.max_receive_message_length', -1)])
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(self.service, self.server)
        # Registrar el método slowDown en el servidor gRPC
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(self.service, self.server)

    async def stop(self):
        await self.server.stop(0)

if __name__ == '__main__':
    asyncio.run(start_servers())