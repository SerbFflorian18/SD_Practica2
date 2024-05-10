import os
import sys


proto_dir = os.path.join(os.path.dirname(__file__), '..','proto')
sys.path.append(proto_dir)

from concurrent import futures
import time
import grpc


import store_pb2_grpc
import store_pb2
from storage_service import StorageService

class StorageServiceServicer(store_pb2_grpc.KeyValueStore):
    

    def __init__(self, is_master = False):
        self.is_master = is_master
        self.delay = 0
        self.storage = StorageService()
        self.master = None
        self.slaves = None


    # Save Key-value 
    def put(self, request, context):
        # Check if this node is the master, otherwise do not save any data in the Storage
        if(self.is_master):
            #print("Do Voting and stuff....")
            success = self.save(request.key, request.value)
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

        # Fetch from the database
        found, value = self.storage.fetch(request.key)
        
        # Construct the response
        response = store_pb2.GetResponse(value=value, found=found)

        return response


    # Slow down The server in seconds
    def slowDown(self, request, context):
        # Set delay to the value of seconds
        self.delay = self.delay + int(request.seconds)

        # Make a response
        response = store_pb2.SlowDownResponse(success=True)

        return response


    # Remove the slowdown delay
    def restore(self, request, context):
        # Set delay to Zero
        self.delay = 0

        # Make a response
        response = store_pb2.RestoreResponse(success=True)

        return response
    

# Create gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

# Add our service to the server
store_pb2_grpc.add_KeyValueStoreServicer_to_server(
    StorageServiceServicer(True),
    server
)

# Listen to the port 32770
print("Starting the server. Listening on port 32770 ....")
server.add_insecure_port('localhost:32770')
server.start()

# since server.start() will not block,
# a sleep-loop is added to keep alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)








