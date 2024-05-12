# client.py
import grpc
import sys
import os
# Add the decentralized proto directory to the Python path
decentralized_dir = os.path.join(os.path.dirname(__file__), 'proto')
sys.path.append(decentralized_dir)

# Import generated gRPC modules
import store_pb2
import store_pb2_grpc

def get_nodes_from_discovery():
    """
    Function to fetch the list of nodes from the discovery server.

    Returns:
        List[store_pb2.Node]: List of node objects.
    """
    try:
        # Establish an insecure gRPC channel to the discovery server
        with grpc.insecure_channel('localhost:50051') as channel:
            # Create a stub for the Discovery service
            stub = store_pb2_grpc.DiscoveryStub(channel)
            # Call the GetNodes RPC method
            response = stub.GetNodes(store_pb2.GetNodesRequest())
            # Return the list of nodes from the response
            return response.nodes
    except grpc.RpcError as e:
        # Handle gRPC errors
        print(f"Error getting nodes from discovery server: {e}")
        return []

if __name__ == "__main__":
    # Call the function to get nodes from the discovery server
    nodes = get_nodes_from_discovery()
    # Print the list of nodes
    print("Nodes from discovery server:", nodes)