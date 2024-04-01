import grpc
import raft_pb2
import raft_pb2_grpc
import random


class RaftClient:
    def __init__(self, node_addresses):
        self.node_addresses = node_addresses
        self.leader_id = "None"
        self.channels = {
            address: grpc.insecure_channel(address) for address in node_addresses
        }
        self.stubs = {
            address: raft_pb2_grpc.RaftNodeStub(channel)
            for address, channel in self.channels.items()
        }

    def send_request(self, request, server_address,flag):
        if self.leader_id == "None":
            try:
                response = self.stubs[self.node_addresses[(server_address)]].ServeClient(
                    raft_pb2.ServeClientArgs(request=request)
                )
                if response.success:
                    self.leader_id = response.leaderID
                    print(f"1-Leader ID: {self.leader_id}")
                    return response.data
                else:
                    print(f"2-Leader ID: {response.leaderID}")
                    while response.leaderID == "None":
                        response = self.stubs[
                            self.node_addresses[server_address]
                        ].ServeClient(raft_pb2.ServeClientArgs(request=request))
                    self.leader_id = response.leaderID
                    response = self.stubs[
                        self.node_addresses[int(self.leader_id)]
                    ].ServeClient(raft_pb2.ServeClientArgs(request=request))
                    return response.data
            except grpc.RpcError as e:
                index = random.randint(0, 4)
                print(f"RPC error: {e}")
                print(index)
                self.send_request(request, index,flag=1)
        else:
            try:
                if flag == 1:
                    response = self.stubs[
                        self.node_addresses[int(server_address)]
                    ].ServeClient(raft_pb2.ServeClientArgs(request=request))
                else:
                    response = self.stubs[
                        self.node_addresses[int(self.leader_id)]
                    ].ServeClient(raft_pb2.ServeClientArgs(request=request))
                if response.success:
                    print(f"3-Leader ID: {response.leaderID}")
                    self.leader_id = response.leaderID
                    return response.data
                else:
                    print(f"4-Leader ID: {response.leaderID}")
                    self.leader_id = response.leaderID
                    if self.leader_id != "None":
                        response = self.stubs[
                            self.node_addresses[int(self.leader_id)]
                        ].ServeClient(raft_pb2.ServeClientArgs(request=request))
                        return response.data
            except grpc.RpcError as e:
                index = random.randint(0, 4)
                print(f"RPC error: {e}")
                self.send_request(request,index,flag=1)

        return ""

    def get(self, key):
        return self.send_request(f"GET {key}", 0,flag=0)

    def set(self, key, value):
        return self.send_request(f"SET {key} {value}", 0,flag=0)


if __name__ == "__main__":
    client = RaftClient(
        [
            "localhost:50051",
            "localhost:50052",
            "localhost:50053",
            "localhost:50054",
            "localhost:50055",
        ]
    )
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
