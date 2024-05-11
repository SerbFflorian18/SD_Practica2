import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../proto')

import grpc
import store_pb2_grpc
import store_pb2


# Open a gRPC channel
channel = grpc.insecure_channel('localhost:32771')

# Create a stub (client)
stub = store_pb2_grpc.KeyValueStoreStub(channel)

# request = store_pb2.PutRequest(key='first', value='newer')
# response = stub.put(request)
# print("res: ", response.success)

try:
    #slow_request = store_pb2.SlowDownRequest(seconds=2)
    #slow_response = stub.slowDown(slow_request)

    #restore_request = store_pb2.RestoreRequest()
    #restore_response = stub.restore(restore_request)

    get_request = store_pb2.GetRequest(key='first')
    get_response = stub.get(get_request)
    print(get_response.value)

except grpc.RpcError as e:
    print("Timeout")
