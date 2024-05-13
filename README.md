# Distributed storage systems and the CAP theorem

The project explores both centralized and decentralized architectures for distributed storage systems, addressing the CAP theorem's implications. 
Through gRPC implementation and API design, it ensures efficient communication and coordination among nodes, while emphasizing consistency, availability, and fault tolerance.

## Features

- **Centralized:** Implementation of the server cluster with a master node and slave nodes for cloud data storage.
- **Decentralized:**  Implementation of a decentralized architecture without a master node, where all nodes collaborate for data storage.

## Use
-  **Centralized:** Execute python file centralized.py
-  **Decentralized:** Execute python file decentralized.py



```
SD_PRACTICA2/
├── _pycache_
|
├── eval/
|   ├── _pycache_
|   ├── eval.py
│   ├── centralized_system_test.py
│   └── decentralized_system_test.py
|
├── proto/
|   ├── _pycache_
│   ├── store.proto
|   ├── center.proto
│   ├── store_pb2.py
│   └── store_pb2_grpc.py
|
├── centeralized/
|   ├── server.py
│   ├── storage_service.py
│   └── test_client.py
|
|
├── decentralized/
|   ├── client.py
│   ├── discoveryServicer.py
│   └── proto/
|       └── desc.proto
|
|
├── centralized_config.yaml
├── centralized.py
|
├── decentralized_config.yaml
├── decentralized.py
|
├── error.log
├── warning.log
|
└── README.md
```

## Directory Structure Explanation

- **proto/**: Contains Protocol Buffer files used for defining gRPC services and messages. Generated Python files (`store_pb2.py` and `store_pb2_grpc.py`) based on `store.proto` should be stored here.

- **centralized_config.yaml and decentralized_config.yaml**: YAML configuration files containing settings for the centralized and decentralized systems.

- **eval/**: Directory containing evaluation scripts and tests.

  - **test_centralized_system.py**: Script containing unit tests for the centralized system.

    - ***Sample***: 

    ```
    master:
      ip: <IP>
      port: <Port>

    slaves:
      - id: <slave_1_ID>
        ip: <slave_1_IP>
        port: <slave_1_Port>
      - id: <slave_2_ID>
        ip: <slave_2_IP>
        port: <slave_2_Port>
      ...
      ```
  
  - **test_decentralized_system.py**: Script containing unit tests for the decentralized system.

      - ***Sample***: 

    ```
    nodes:
      - id: <node_1_ID>
        ip: <node_1_IP>
        port: <node_1_Port>
      - id: <node_2_ID>
        ip: <node_2_IP>
        port: <node_2_Port>
      ...
      ```

Each component of the project is organized into its respective directory, facilitating clear separation of concerns and ease of navigation. The `eval` directory specifically houses test scripts for evaluating the functionality and correctness of the implemented systems.

> **Note:** Students are required to define the necessary stubs for implementing the Two Phase Commit (2PC) protocol and for node registration in the system. These stubs must be manually added to the store.proto file by the students as part of their implementation.
