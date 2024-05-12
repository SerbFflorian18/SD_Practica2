import grpc
import sys
import os
from concurrent import futures

# Import gRPC generated code for service and server
decentralized_dir = os.path.join(os.path.dirname(__file__), 'decentralized/proto')
sys.path.append(decentralized_dir)
import store_pb2
import store_pb2_grpc

class DiscoveryServicer(store_pb2_grpc.DiscoveryServicer):
    def __init__(self):
        self.nodes = []

    def RegisterNode(self, request, context):
        # Register a new node
        self.nodes.append(request)
        print(f"Node {request.node_id} registered with IP {request.ip} and port {request.port}")
        return store_pb2.RegisterResponse(success=True)

    def GetNodes(self, request, context):
        # Return the list of registered nodes
        return store_pb2.GetNodesResponse(nodes=self.nodes)

def serve():
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add DiscoveryServicer to the server
    store_pb2_grpc.add_DiscoveryServicer_to_server(DiscoveryServicer(), server)
    
    # Bind server to port 50051
    server.add_insecure_port('[::]:50051')
    
    # Start the server
    server.start()
    print("Discovery server started on port 50051")
    
    # Keep the server running until terminated
    server.wait_for_termination()

if __name__ == '__main__':
    # Run the server
    serve()