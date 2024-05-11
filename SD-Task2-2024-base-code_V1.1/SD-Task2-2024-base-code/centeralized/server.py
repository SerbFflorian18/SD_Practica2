import concurrent
import sys
import os

import yaml

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../proto')

from concurrent import futures
import time
import grpc

import store_pb2_grpc
import store_pb2

import center_pb2_grpc
import center_pb2

from .storage_service import StorageService


# Server Node class to save data of a node
class Node:
    def __init__(self, id_, ip, port):
        self.id = id_
        self.ip = ip
        self.port = port
        channel = grpc.insecure_channel(f'{ip}:{port}')
        self.stub = center_pb2_grpc.InternalProtocolStub(channel)


class StorageServiceServicer(store_pb2_grpc.KeyValueStore, center_pb2_grpc.InternalProtocol):
    def __init__(self, is_master=False, slave_id=0):
        self.is_master = is_master
        self.delay = 0
        self.storage = StorageService()
        self.server = None
        self.master = None
        self.nodes = list()
        self.config = self.load_config()
        self.id = slave_id
        self.ip = self.config['slaves'][slave_id]['ip'] if not is_master else self.config['master']['ip']
        self.port = self.config['slaves'][slave_id]['port'] if not is_master else self.config['master']['port']
        self.master_stub = None

        # save the  master in the list
        self.nodes.append(Node(self.id, self.ip, self.port))

        # Connect to master:
        if not is_master:
            # Open a gRPC channel
            channel = grpc.insecure_channel(f'{self.config["master"]["ip"]}:{self.config["master"]["port"]}')
            # Create a stub to the master
            self.master_stub = center_pb2_grpc.InternalProtocolStub(channel)
            self.send_info()

    def load_config(self):

        config_path = os.path.dirname(os.path.abspath(__file__)) + '/../centralized_config.yaml'
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    # Save Key-value
    def put(self, request, context):
        # Add delay
        time.sleep(self.delay)

        # Check if this node is the master, otherwise do not save any data in the Storage
        if self.is_master:

            # Send vote request to all nodes
            vote = self.multicastCanCommit()

            if vote:
                # If they all agree we send a do commit
                success = self.multicastDoCommit(request.key, request.value)
            else:
                success = False

            response = store_pb2.PutResponse(success=success)

        else:
            # We can not accept put requests in a slave node
            response = store_pb2.PutResponse(success=False)

        return response

    def save(self, key, value):
        # Tem function
        success = self.storage.save(key, value)
        return success

    # Get the value of the key
    def get(self, request, context):
        # Add delay
        time.sleep(self.delay)

        # Fetch from the database
        found, value = self.storage.fetch(request.key)

        # Construct the response
        response = store_pb2.GetResponse(value=value, found=found)

        return response

    # Slow down The server in seconds
    def slowDown(self, request, context):
        # Add delay
        time.sleep(self.delay)

        # Set delay to the value of seconds
        self.delay = self.delay + int(request.seconds)

        # Make a response
        response = store_pb2.SlowDownResponse(success=True)

        return response

    # Remove the slowdown delay
    def restore(self, request, context):
        # Add delay
        time.sleep(self.delay)

        # Set delay to Zero
        self.delay = 0

        # Make a response
        response = store_pb2.RestoreResponse(success=True)

        return response

    def start_server(self):

        # Create gRPC server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Add our service to the server
        store_pb2_grpc.add_KeyValueStoreServicer_to_server(
            self,
            self.server
        )

        # Add protocol to the server
        center_pb2_grpc.add_InternalProtocolServicer_to_server(
            self,
            self.server
        )

        # Listen to the port 32770
        # print(f'Starting the server. Listening on port {self.port} ....')
        self.server.add_insecure_port(f'{self.ip}:{self.port}')
        self.server.start()

    # 2PC protocol functions ##################################################
    def notifyMaster(self, request, context):
        # Add delay
        time.sleep(self.delay)

        # Save in list of nodes
        self.nodes.append(Node(request.id, request.ip, request.port))

        # Response
        response = center_pb2.notifyMasterResponse(ack=True)
        return response

    # Send our info to the server
    def send_info(self):
        # Create and send the request
        info = center_pb2.notifyMasterRequest(id=self.id, ip=self.ip, port=self.port)
        # Get the response
        response = self.master_stub.notifyMaster(info)
        # if response.ack:
        #     print("Connected to the master.")
        # else:
        #     print("We could not connect to the sever.")

    # Multicast can Commit to all nodes
    def multicastCanCommit(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            fs = list()
            for node in self.nodes:
                req = center_pb2.canCommitRequest()
                future = executor.submit(node.stub.canCommit, req)
                fs.append(future)

            concurrent.futures.wait(fs)
            # Get The vote results
            res = list(map(lambda x: x.result().ack, fs))
            votes = True
            for v in res:
                if not v:
                    votes = False
                    break

        return votes

    # canCommit grpc
    def canCommit(self, request, context):
        # Add delay
        time.sleep(self.delay)

        #print("Can Commit? yes")
        response = center_pb2.canCommitResponse(ack=True)
        return response

        # canCommit grpc

    def multicastDoCommit(self, key, value):
        # Add delay
        time.sleep(self.delay)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            fs = list()
            for node in self.nodes:
                req = center_pb2.doCommitRequest(key=key, value=value)
                future = executor.submit(node.stub.doCommit, req)
                fs.append(future)

            concurrent.futures.wait(fs)
            # Get The vote results
            res = list(map(lambda x: x.result().ack, fs))
            votes = True
            for v in res:
                if not v:
                    votes = False
                    break

        return votes
    def doCommit(self, request, context):

        # Add delay
        time.sleep(self.delay)

        state = self.save(request.key, request.value)

        #print("Committed")

        response = center_pb2.doCommitResponse(ack=state)
        return response


# test a node
# node = StorageServiceServicer(True, 0)
# node.start_server()
# # since server.start() will not block,
# # a sleep-loop is added to keep alive
# try:
#     while True:
#         time.sleep(86400)
# except KeyboardInterrupt:
#     node.server.stop(0)
