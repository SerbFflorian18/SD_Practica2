import asyncio
import time

from centeralized.server import StorageServiceServicer

async def main():
    # Create The master node
    node_master = StorageServiceServicer(True, 0)
    node_master.start_server()

    # Create the slave node 1
    node_1 = StorageServiceServicer(False, 0)
    node_1.start_server()

    # Create the slave node 2
    node_2 = StorageServiceServicer(False, 1)
    node_2.start_server()

    #node_1.server.stop(0)



    # since server.start() will not block,
    # a sleep-loop is added to keep alive
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        node_master.server.stop(0)
        node_1.server.stop(0)
        node_2.server.stop(0)

if __name__ == '__main__':
    asyncio.run(main())

