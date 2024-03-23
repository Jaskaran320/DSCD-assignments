import os
import shutil
import grpc
import raft_pb2_grpc
from node import RaftNode
from concurrent import futures

if __name__ == "__main__":
    num_nodes = 5
    # if os.path.exists("logs"):
    #     shutil.rmtree("logs")
    ports = [50051, 50052, 50053, 50054, 50055]
    servers = []

    try:
        for node_id, port in enumerate(ports):
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            raft_node_instance = RaftNode(node_id, num_nodes)
            raft_pb2_grpc.add_RaftNodeServicer_to_server(raft_node_instance, server)
            server.add_insecure_port(f"[::]:{port}")
            server.start()
            print(f"Raft node {node_id} started on port {port}")
            servers.append(server)

        for server in servers:
            server.wait_for_termination()

    except KeyboardInterrupt:
        print("Shutting down servers...")
        for server in servers:
            server.stop(None)
