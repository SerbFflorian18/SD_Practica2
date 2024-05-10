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

import random



_ONE_DAY_IN_SECONDS = 60 * 60 * 24



class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):

    def __init__(self, node_id, nodes):

        self.node_id = node_id

        self.nodes = nodes

        self.data = {}  

        self.lock = asyncio.Lock()  



    async def put(self, request, context):

        async with self.lock:  

            await self.propagate_put(request)

        return store_pb2.PutResponse(success=True)  



    async def get(self, request, context):

        async with self.lock:  

            value = self.data.get(request.key, "")

        return store_pb2.GetResponse(value=value, found=bool(value))  



    async def replicate(self, request):

        quorum_size = 3 if request.value else 2  

        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))  

        for node in nodes:

            if node != self.node_id:

                try:

                    async with grpc.aio.insecure_channel(node) as channel:

                        stub = store_pb2_grpc.KeyValueStoreStub(channel)

                        await stub.put(store_pb2.PutRequest(key=request.key, value=request.value))

                except grpc.RpcError as e:

                    logging.error("Error replicating to %s: %s", node, e)



    async def ask_vote(self, request, context):

        vote = self.node_id

        return store_pb2.VoteResponse(vote=vote)



    async def do_commit(self, request, context):

        async with self.lock:  

            self.data[request.key] = request.value



    async def propagate_put(self, request):

        try:

            # Gather votes from other nodes

            votes = await asyncio.gather(*[self.request_vote(node, request) for node in self.nodes if node != self.node_id])

            # Count votes

            num_votes = sum(vote.vote == self.node_id for vote in votes) + 1  # Add 1 for own vote

            # Check if quorum is reached

            if num_votes >= 3:  # Quorum size for writes

                # If quorum is reached, propagate commit to all nodes

                await asyncio.gather(*[self.commit_to_node(node, request) for node in self.nodes])

        except Exception as e:

            logging.error("Error in propagate_put: %s", e)



    async def request_vote(self, node, request):

        async with grpc.aio.insecure_channel(node) as channel:

            stub = store_pb2_grpc.KeyValueStoreStub(channel)

            return await stub.ask_vote(store_pb2.VoteRequest(key=request.key))



    async def commit_to_node(self, node, request):

        async with grpc.aio.insecure_channel(node) as channel:

            stub = store_pb2_grpc.KeyValueStoreStub(channel)

            await stub.do_commit(store_pb2.CommitRequest(key=request.key, value=request.value))



    async def propagate_get(self, request):

        try:

            # Gather values from other nodes

            values = await asyncio.gather(*[self.request_value(node, request) for node in self.nodes if node != self.node_id])

            # Filter out empty values

            values = [value.value for value in values if value.value]

            # If any node has the value, return it

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



class Server:

    def __init__(self, node_id, ip, port, nodes):

        self.node_id = node_id

        self.ip = ip

        self.port = port

        self.nodes = nodes

        self.server = grpc.aio.server(options=[('grpc.max_send_message_length', -1), ('grpc.max_receive_message_length', -1)])

        store_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStore(self.node_id, self.nodes), self.server)



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

            nodes = [f"{n['ip']}:{n['port']}" for n in config['nodes'] if n != node]

            server = Server(node_id, ip, port, nodes)

            server_address = f"{ip}:{port}"

            server.server.add_insecure_port(server_address)

            await server.server.start()

            servers.append(server)

            logging.info(f"Server for node {node_id} listening on {server_address}")

        await asyncio.gather(*[server.server.wait_for_termination() for server in servers])

    except KeyboardInterrupt:

        logging.info("Stopping servers...")

        await asyncio.gather(*[server.server.stop(0) for server in servers])

    finally:

        logging.info("Closing all servers...")



signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(start_servers()))



if __name__ == '__main__':

    asyncio.run(start_servers())