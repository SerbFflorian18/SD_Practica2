import os
import sys


proto_dir = os.path.join(os.path.dirname(__file__), '..','proto')
sys.path.append(proto_dir)

import grpc
import store_pb2_grpc
import store_pb2


# Open a gRPC channel
channel = grpc.insecure_channel('localhost:32770')

# Create a stub (client)
stub = store_pb2_grpc.KeyValueStoreStub(channel)

#request = store_pb2.PutRequest(key='first', value='newer')
#response = stub.put(request)
#print(response.success)

get_request = store_pb2.GetRequest(key='first')
get_response = stub.get(get_request)
print(get_response.value)