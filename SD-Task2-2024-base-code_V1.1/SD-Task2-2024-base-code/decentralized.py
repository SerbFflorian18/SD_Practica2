import signal
import sys
import logging
import os
import grpc
from grpc.experimental import aio as grpc_aio  # type: ignore
#python -m grpc_tools.protoc -I./ --python_out=. --grpc_python_out=. ./store.proto
#python .\eval\decentralized_system_tests.py
#python .\decentralized.py
#source .venv/bin/activate
proto_dir = os.path.join(os.path.dirname(__file__), 'proto')
sys.path.append(proto_dir)
import store_pb2
import store_pb2_grpc
import yaml
import asyncio
import json
import random
from datetime import datetime

# Paths for error and warning log files
log_dir = os.path.dirname(__file__)
error_log_path = os.path.join(log_dir, 'error.log')
warning_log_path = os.path.join(log_dir, 'warning.log')

# Configure log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configure error logger
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(error_log_path, mode='w')
error_handler.setFormatter(formatter)
error_logger.addHandler(error_handler)

# Configure warning logger
warning_logger = logging.getLogger('warning_logger')
warning_logger.setLevel(logging.WARNING)
warning_handler = logging.FileHandler(warning_log_path, mode='w')
warning_handler.setFormatter(formatter)
warning_logger.addHandler(warning_handler)

# Configure logging to capture all exceptions and errors
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[error_handler, warning_handler])

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class KeyValueStore(store_pb2_grpc.KeyValueStoreServicer):
    """
    Implementation of the KeyValueStore service.
    """

    def __init__(self, node_id, nodes):
        """
        Initialize the KeyValueStore service.

        Args:
            node_id (str): The ID of the current node.
            nodes (list): List of node addresses in the network.
        """
        self.node_id = node_id
        self.nodes = nodes
        self.data = {}
        self.lock = asyncio.Lock()  # Lock for read and write operations

    async def put(self, request, context):
        """
        Put method for storing key-value pairs.

        Args:
            request (store_pb2.PutRequest): The request containing key and value.
            context: RPC context.

        Returns:
            store_pb2.PutResponse: The response indicating success.
        """
        async with self.lock:
            self.data[request.key] = request.value
            await self.persist_data()
            await self.propagate_put(request)
        return store_pb2.PutResponse(success=True)

    async def get(self, request, context):
        """
        Get method for retrieving the value associated with a key.

        Args:
            request (store_pb2.GetRequest): The request containing the key.
            context: RPC context.

        Returns:
            store_pb2.GetResponse: The response containing the value (if found).
        """
        async with self.lock:
            value = self.data.get(request.key, "")
        return store_pb2.GetResponse(value=value, found=bool(value))

    async def persist_data(self):
        """
        Persist the data to a JSON file.
        """
        try:
            with open('data.json', 'w') as file:
                json.dump(self.data, file)
        except FileNotFoundError as e:
            error_logger.error("Failed to find data file: %s", e)
        except PermissionError as e:
            error_logger.error("Permission denied to write to data file: %s", e)
        except Exception as e:
            error_logger.error("Error persisting data: %s", e)

    async def recover_data(self):
        """
        Recover data from the JSON file.
        """
        try:
            with open('data.json', 'r') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            warning_logger.warning("Data file not found. Starting with empty data.")
        except Exception as e:
            error_logger.error("Error recovering data: %s", e)

    async def replicate(self, request):
        """
        Replicate the put operation to other nodes.

        Args:
            request (store_pb2.PutRequest): The put request.
        """
        quorum_size = 3 if request.value else 2
        nodes = random.sample(self.nodes, min(len(self.nodes), quorum_size))
        for node in nodes:
            if node != self.node_id:
                await self.propagate_put(request)

    async def propagate_put(self, request):
        """
        Propagate the put operation to other nodes.

        Args:
            request (store_pb2.PutRequest): The put request.
        """
        try:
            quorum_size = max(2, len(self.nodes) // 2 + 1)
            nodes = random.sample(self.nodes, quorum_size)
            votes = await asyncio.gather(*[self.request_vote(node, request) for node in nodes])
            num_votes = sum(1 for vote in votes if vote.vote == self.node_id) + 1
            if num_votes >= quorum_size:
                await self.confirm_to_node(self.node_id, request)
        except Exception as e:
            if not isinstance(e, TypeError):
                error_logger.error("Error propagating modification: %s", e)

    async def request_vote(self, node, request):
        """
        Request a vote from a node.

        Args:
            node (str): Node address.
            request (store_pb2.PutRequest): The put request.

        Returns:
            store_pb2.VoteResponse: The vote response.
        """
        return await self.ask_for_vote(request, None)

    async def confirm_to_node(self, node, request):
        """
        Confirm the put operation to a node.

        Args:
            node (str): Node address.
            request (store_pb2.PutRequest): The put request.
        """
        async with grpc_aio.insecure_channel(node) as channel:
            stub = store_pb2_grpc.KeyValueStoreStub(channel)
            await stub.do_commit(store_pb2.CommitRequest(key=request.key, value=request.value))

    async def propagate_get(self, request):
        """
        Propagate the get operation to other nodes.

        Args:
            request (store_pb2.GetRequest): The get request.

        Returns:
            str: The value retrieved from other nodes.
        """
        try:
            values = await asyncio.gather(*[self.request_value(node, request) for node in self.nodes if node != self.node_id])
            values = [value.value for value in values if value.value]
            if values:
                return values[0]
            else:
                return None
        except Exception as e:
            error_logger.error("Error propagating query: %s", e)
            return None

    async def request_value(self, node, request):
        """
        Request the value associated with a key from a node.

        Args:
            node (str): Node address.
            request (store_pb2.GetRequest): The get request.

        Returns:
            store_pb2.GetResponse: The response containing the value.
        """
        async with grpc_aio.insecure_channel(node) as channel:
            stub = store_pb2_grpc.KeyValueStoreStub(channel)
            return await stub.get(store_pb2.GetRequest(key=request.key))

    async def ask_for_vote(self, request, context):
        """
        Ask a node for a vote.

        Args:
            request (store_pb2.PutRequest): The put request.
            context: RPC context.

        Returns:
            store_pb2.VoteResponse: The vote response.
        """
        return store_pb2.VoteResponse(vote=self.node_id)

    async def slowDown(self, request, context):
        """
        Add delay to operations.

        Args:
            request (store_pb2.SlowDownRequest): The request containing delay.
            context: RPC context.

        Returns:
            store_pb2.SlowDownResponse: The response indicating success or failure.
        """
        try:
            delay = request.delay
            await asyncio.sleep(delay)
            return store_pb2.SlowDownResponse(success=True)
        except asyncio.CancelledError:
            warning_logger.info("Delay operation cancelled")
            return store_pb2.SlowDownResponse(success=False)
        except Exception as e:
            error_logger.error("Error in slowDown: %s", e)
            return store_pb2.SlowDownResponse(success=False)

    async def restore(self, request, context):
        """
        Restore the node's data from the data file.

        Args:
            request: The restore request.
            context: RPC context.

        Returns:
            store_pb2.RestoreResponse: The response indicating success or failure.
        """
        try:
            await self.recover_data()
            return store_pb2.RestoreResponse(success=True)
        except Exception as e:
            error_logger.error("Error restoring node: %s", e)
            return store_pb2.RestoreResponse(success=False)

async def load_configuration(config_path):
    """
    Load configuration from YAML file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Loaded configuration.
    """
    try:
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        error_logger.error("Configuration file not found at specified path: %s", config_path)
        return {}
    except Exception as e:
        error_logger.error("Error loading configuration: %s", e)
        return {}

async def start_servers():
    """
    Start gRPC servers for each node defined in the configuration.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'decentralized_config.yaml')
    config = await load_configuration(config_path)
    servers = []
    try:
        for node in config['nodes']:
            node_id = node['id']
            ip = node['ip']
            port = node['port']
            nodes = [f"{n['ip']}:{n['port']}" for n in config['nodes'] if n != node and 'ip' in n and 'port' in n]
            service = KeyValueStore(node_id, nodes)
            await service.recover_data()  # Recover data from disk on startup
            server = Server(service, ip, port)
            server_address = f"{ip}:{port}"
            try:
                server.server.add_insecure_port(server_address)
            except Exception as e:
                error_logger.error("Error adding port to server: %s", e)
                continue  # Continue to next iteration if error occurs
            try:
                await server.server.start()
            except Exception as e:
                error_logger.error("Error starting server: %s", e)
                continue  # Continue to next iteration if error occurs
            else:
                servers.append(server)
                logging.info(f"Server for node {node_id} listening on {server_address}")
        # Handle interrupt signal (Ctrl+C)
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown(servers)))

        await asyncio.gather(*[server.server.wait_for_termination() for server in servers])
    finally:
        logging.info("Closing all servers...")

async def shutdown(servers):
    """
    Shutdown all servers.

    Args:
        servers (list): List of server instances.
    """
    for server in servers:
        await server.stop()

class Server:
    """
    gRPC Server wrapper class.
    """

    def __init__(self, service, ip, port):
        """
        Initialize the gRPC Server.

        Args:
            service (KeyValueStore): The KeyValueStore service instance.
            ip (str): IP address to bind.
            port (int): Port to bind.
        """
        self.service = service
        self.ip = ip
        self.port = port
        self.server = grpc_aio.server(options=[('grpc.max_send_message_length', -1), ('grpc.max_receive_message_length', -1)])
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(self.service, self.server)

    async def stop(self):
        """
        Stop the gRPC server.
        """
        await self.server.stop(None)

if __name__ == '__main__':
    # Set global logging level to avoid printing specific error messages
    logging.getLogger().setLevel(logging.ERROR)
    asyncio.run(start_servers())