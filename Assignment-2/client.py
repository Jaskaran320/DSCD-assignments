import grpc
import raft_pb2
import raft_pb2_grpc


class RaftClient:
    def __init__(self, node_addresses):
        self.node_addresses = node_addresses
        self.leader_id = None
        self.channels = {
            address: grpc.insecure_channel(address) for address in node_addresses
        }
        self.stubs = {
            address: raft_pb2_grpc.RaftNodeStub(channel)
            for address, channel in self.channels.items()
        }

    def send_request(self, request):
        for node_address, stub in self.stubs.items():
            try:
                response = stub.ServeClient(raft_pb2.ServeClientArgs(request=request))
                if response.success:
                    self.leader_id = response.leaderID
                    return response.data
                elif response.leaderID:
                    self.leader_id = response.leaderID
            except grpc.RpcError as e:
                print(f"RPC error: {e}")
        return None

    def get(self, key):
        return self.send_request(f"GET {key}")

    def set(self, key, value):
        return self.send_request(f"SET {key} {value}")
    

if __name__ == "__main__":
    client = RaftClient(["localhost:50051", "localhost:50052", "localhost:50053", "localhost:50054", "localhost:50055"])
    while True:
        print("1. Get")
        print("2. Set")
        print("3. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            key = input("Enter key: ")
            print(f"Value: {client.get(key)}")
        elif choice == "2":
            key = input("Enter key: ")
            value = input("Enter value: ")
            print(f"Set: {client.set(key, value)}")
        elif choice == "3":
            break
        else:
            print("Invalid choice")