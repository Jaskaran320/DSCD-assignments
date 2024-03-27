import os
import grpc
import random
import time
import threading
import shutil
from collections import defaultdict
from concurrent import futures
import raft_pb2
import raft_pb2_grpc


class RaftNode(raft_pb2_grpc.RaftNodeServicer):
    def __init__(self, node_id, num_nodes):
        self.node_id = node_id
        self.num_nodes = num_nodes
        self.state = "FOLLOWER"
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_length = 0
        self.leader_id = None
        self.next_index = defaultdict(lambda: 0)
        self.match_index = defaultdict(lambda: 0)
        self.election_timeout = random.uniform(5, 10)
        self.heartbeat_timeout = 1
        self.lease_timeout = 4
        self.lease_acquired = False
        self.lease_start_time = 0
        self.old_leader_lease_end_time = 0

        self.create_persistent_storage()
        self.load_persistent_state()
        self.start_election_timer()
        self.start_heartbeat_timer()
        self.start_lease_renewal_timer()

    def create_persistent_storage(self):
        dir_name = f"logs/logs_node_{self.node_id}"
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        self.log_file = open(os.path.join(dir_name, "logs.txt"), "a+")
        self.metadata_file = open(os.path.join(dir_name, "metadata.txt"), "a+")
        self.dump_file = open(os.path.join(dir_name, "dump.txt"), "a+")

    def load_persistent_state(self):
        self.log_file.seek(0)
        self.metadata_file.seek(0)
        for line in self.log_file:
            entry = line.strip().split()
            if entry[0] == "SET":
                self.log.append((entry[0], entry[1], entry[2], int(entry[3])))
            elif entry[0] == "NO-OP":
                self.log.append((entry[0], "", "", int(entry[1])))
        for line in self.metadata_file:
            metadata = line.strip().split()
            self.current_term = int(metadata[0])
            self.voted_for = metadata[1]
            self.commit_length = int(metadata[2])

    def persist_log(self, entry):
        self.log_file.write(
            f"{entry.operation} {entry.key} {entry.value} {entry.term}\n"
        )
        self.log_file.flush()

    def persist_metadata(self):
        self.metadata_file.write(
            f"{self.current_term} {self.voted_for} {self.commit_length}\n"
        )
        self.metadata_file.flush()

    def start_election_timer(self):
        self.election_timer = threading.Timer(
            self.election_timeout, self.start_election
        )
        self.election_timer.start()

    def start_heartbeat_timer(self):
        self.heartbeat_timer = threading.Timer(
            self.heartbeat_timeout, self.send_heartbeat
        )
        self.heartbeat_timer.start()

    def start_lease_renewal_timer(self):
        self.lease_renewal_timer = threading.Timer(self.lease_timeout, self.renew_lease)
        self.lease_renewal_timer.start()

    def restart_election_timer(self):
        self.election_timer.cancel()
        self.election_timeout = random.uniform(5, 10)
        self.start_election_timer()

    def restart_heartbeat_timer(self):
        self.heartbeat_timer.cancel()
        self.start_heartbeat_timer()

    def restart_lease_renewal_timer(self):
        if self.lease_acquired:
            self.lease_renewal_timer.cancel()
        self.start_lease_renewal_timer()

    def start_election(self):
        self.dump_file.write(
            f"Node {self.node_id} election timer timed out, Starting election.\n"
        )
        self.dump_file.flush()
        self.state = "CANDIDATE"
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes = 1
        self.persist_metadata()
        self.send_request_vote()

    def send_request_vote(self):
        request = raft_pb2.RequestVoteArgs(
            term=self.current_term,
            candidateID=str(self.node_id),
            lastLogIndex=len(self.log),
            lastLogTerm=self.log[-1][3] if self.log else 0,
        )
        for node_id in range(self.num_nodes):
            if node_id != self.node_id:
                try:
                    stub = self.get_stub(node_id)
                    response = stub.RequestVote(request)
                    if (
                        response.voteGranted
                        and self.state == "CANDIDATE"
                        and self.current_term == response.term
                    ):
                        self.votes += 1
                        print(
                            f"Vote granted to Node {self.node_id} in term {self.current_term} by Node {node_id}."
                        )
                        self.dump_file.write(
                            f"Vote granted to Node {self.node_id} in term {self.current_term} by Node {node_id}.\n"
                        )
                        self.dump_file.flush()
                    else:
                        self.dump_file.write(
                            f"Vote denied to Node {self.node_id} in term {self.current_term} by Node {node_id}.\n"
                        )
                        self.dump_file.flush()
                        self.state = "FOLLOWER"
                        self.current_term = response.term
                        self.voted_for = None
                        # self.election_timer.cancel()
                        # self.restart_election_timer()
                    self.old_leader_lease_end_time = max(
                        self.old_leader_lease_end_time, response.oldLeaderLeaseDuration
                    )
                except grpc.RpcError:
                    self.dump_file.write(
                        f"send_request_vote Error occurred while sending RPC to Node {node_id}.\n"
                    )
                    self.dump_file.flush()

        if self.votes > self.num_nodes // 2:
            self.become_leader()

    def become_leader(self):
        self.dump_file.write(
            f"Node {self.node_id} became the leader for term {self.current_term}.\n"
        )
        self.dump_file.flush()
        self.state = "LEADER"
        self.leader_id = self.node_id
        # self.election_timer.cancel()
        # self.restart_election_timer()
        self.next_index = defaultdict(lambda: len(self.log) + 1)
        self.match_index = defaultdict(lambda: 0)
        self.acquire_lease(flag=True)
        self.send_heartbeat()

    def acquire_lease(self, flag=False):
        self.lease_acquired = True
        self.lease_start_time = time.time()
        self.old_leader_lease_end_time = max(
            self.old_leader_lease_end_time, self.lease_start_time + self.lease_timeout
        )
        self.dump_file.write(f"New Leader waiting for Old Leader Lease to timeout.\n")
        self.dump_file.flush()
        while time.time() < self.old_leader_lease_end_time:
            time.sleep(0.1)
        if flag:
            self.append_noop_entry()

    def append_noop_entry(self):
        entry = raft_pb2.Entry(
            operation="NO-OP", key="", value="", term=self.current_term
        )
        self.log.append(("NO-OP", "", "", self.current_term))
        self.persist_log(entry)
        self.send_append_entries(entry)

    def send_heartbeat(self):
        if self.state != "LEADER":
            return

        self.dump_file.write(
            f"Leader {self.node_id} sending heartbeat & Renewing Lease\n"
        )
        self.dump_file.flush()
        self.acquire_lease()
        self.restart_lease_renewal_timer()

        entry = raft_pb2.Entry(
            operation="NO-OP", key="", value="", term=self.current_term
        )
        args = raft_pb2.AppendEntriesArgs(
            term=self.current_term,
            leaderID=str(self.node_id),
            prevLogIndex=len(self.log) - 1,
            prevLogTerm=self.log[-1][3] if self.log else 0,
            entries=[entry],
            leaderCommit=self.commit_length,
            leaseDuration=self.lease_timeout,
        )

        for node_id in range(self.num_nodes):
            if node_id != self.node_id:
                try:
                    stub = self.get_stub(node_id)
                    response = stub.AppendEntries(args)
                    print("Sending from send_heartbeat, node", self.node_id)
                    if response.success:
                        self.match_index[node_id] = args.prevLogIndex + len(args.entries)
                        self.next_index[node_id] = self.match_index[node_id] + 1
                    else:
                        self.next_index[node_id] -= 1
                except grpc.RpcError:
                    self.dump_file.write(
                        f"send_heartbeat Error occurred while sending RPC to Node {node_id}.\n"
                    )
                    self.dump_file.flush()

        # self.check_commit_length()
        self.restart_heartbeat_timer()

    def send_append_entries(self, entry):
        # prev_log_index = len(self.log) - 1
        # prev_log_term = self.log[-1][3] if self.log else 0
        if entry.operation != "SET" and (not self.log or self.log[-1] != (entry.operation, entry.key, entry.value, entry.term)):
            self.log.append((entry.operation, entry.key, entry.value, entry.term))
            self.persist_log(entry)

        # time.sleep(self.heartbeat_timeout)
        # self.restart_heartbeat_timer()

        for node_id in range(self.num_nodes):
            if node_id != self.node_id:
                next_index = self.next_index[node_id]
                prev_log_index = next_index - 1
                prev_log_term = (
                    self.log[prev_log_index][3]
                    if self.log
                    and prev_log_index >= 0
                    and prev_log_index < len(self.log)
                    else 0
                )
                entries = [
                    raft_pb2.Entry(
                        operation=entry[0], key=entry[1], value=entry[2], term=entry[3]
                    )
                    for entry in self.log[next_index:]
                ]
                args = raft_pb2.AppendEntriesArgs(
                    term=self.current_term,
                    leaderID=str(self.node_id),
                    prevLogIndex=prev_log_index,
                    prevLogTerm=prev_log_term,
                    entries=entries,
                    leaderCommit=self.commit_length,
                    leaseDuration=self.lease_timeout,
                )
                try:
                    stub = self.get_stub(node_id)
                    response = stub.AppendEntries(args)
                    print("Sending from send_append_entries", self.node_id)
                    # self.log_file.write(
                    #     f"Node {node_id} received AppendEntries RPC from {self.node_id}.\n"
                    # )
                    # self.log_file.flush()
                    if response.success:
                        self.match_index[node_id] = prev_log_index + len(args.entries)
                        self.next_index[node_id] = self.match_index[node_id] + 1
                        # self.check_commit_length()
                        self.commit_entry(entry)
                        self.dump_file.write(
                            f"Node {node_id} accepted AppendEntries RPC from {self.node_id}.\n"
                        )
                        self.dump_file.flush()
                    else:
                        self.next_index[node_id] = max(0, self.next_index[node_id] - 1)
                        self.dump_file.write(
                            f"Node {node_id} rejected AppendEntries RPC from {self.node_id}.\n"
                        )
                        self.dump_file.flush()
                except grpc.RpcError:
                    self.dump_file.write(
                        f"send_append_entries Error occurred while sending RPC to Node {node_id}.\n"
                    )
                    self.dump_file.flush()

        self.check_commit_length(entry)
        # self.commit_entry(entry)

    # def check_commit_length(self):
    #     print(f"Match Index: {self.match_index}")
    #     committed_entries = sorted(
    #         (
    #             index
    #             for index, entry in self.match_index.items()
    #             if entry > self.commit_length
    #         ),
    #         reverse=True,
    #     )[: self.num_nodes // 2]
    #     print(f"Committed Entries: {committed_entries}")
    #     if committed_entries:
    #         new_commit_length = committed_entries[0]
    #         print(f"Old commit length: {self.commit_length}")
    #         print(f"New commit length: {new_commit_length}")
    #         print(f"Log: {self.log}")
    #         for i in range(self.commit_length + 1, new_commit_length + 1):
    #             entry = self.log[i - 1]
    #             self.commit_entry(entry, log=True)
    #         self.commit_length = new_commit_length

    def check_commit_length(self, entry):
        print(f"Match Index: {self.match_index}")

        match_indices = list(self.match_index.values()) + [len(self.log)]
        match_indices.sort(reverse=True)

        committed_entries = match_indices[: self.num_nodes // 2 + 1]
        print(f"Committed Entries: {committed_entries}")

        if committed_entries:
            new_commit_length = min(committed_entries)
            print(f"Old commit length: {self.commit_length}")
            print(f"New commit length: {new_commit_length}")
            print(f"Log: {self.log}")

            if (
                new_commit_length > self.commit_length
                and self.log[new_commit_length - 1][3] == self.current_term
            ):

                for i in range(self.commit_length + 1, new_commit_length + 1):
                    entry = self.log[i - 1]
                    self.commit_entry(entry, log=True)
                self.commit_length = new_commit_length
            else:
                if entry:
                    self.commit_entry(entry, log=False)

    def commit_entry(self, entry, log=False):
        if log:
            operation, key, value, _ = entry
        else:
            operation = entry.operation
            key = entry.key
            value = entry.value

        if operation == "SET":
            self.dump_file.write(
                f"Node {self.node_id} (leader) committed the entry SET {key} {value} to the state machine.\n"
            )
            self.dump_file.flush()
        elif operation == "NO-OP":
            self.dump_file.write(
                f"Node {self.node_id} (leader) committed the entry NO-OP to the state machine.\n"
            )
            self.dump_file.flush()

    def get_stub(self, node_id):
        address = f"localhost:{50051 + node_id}"
        channel = grpc.insecure_channel(address)
        stub = raft_pb2_grpc.RaftNodeStub(channel)
        return stub

    def ServeClient(self, request, context):
        request_parts = request.request.split()
        operation = request_parts[0]
        if operation == "GET":
            key = request_parts[1]
            value = self.get_value(key)
            if self.state == "LEADER" and self.lease_acquired:
                self.dump_file.write(
                    f"Node {self.node_id} (leader) received a GET {key} request.\n"
                )
                self.dump_file.flush()
                return raft_pb2.ServeClientReply(
                    data=value, leaderID=str(self.node_id), success=True
                )
            else:
                self.dump_file.write(
                    f"Node {self.node_id} received a GET {key} request but is not the leader.\n"
                )
                self.dump_file.flush()
                return raft_pb2.ServeClientReply(
                    data="", leaderID=str(self.leader_id), success=False
                )
        elif operation == "SET":
            key = request_parts[1]
            value = request_parts[2]
            if self.state == "LEADER" and self.lease_acquired:
                self.dump_file.write(
                    f"Node {self.node_id} (leader) received a SET {key} {value} request.\n"
                )
                self.dump_file.flush()
                entry = raft_pb2.Entry(
                    operation="SET", key=key, value=value, term=self.current_term
                )
                self.log.append(("SET", key, value, self.current_term))
                self.persist_log(entry)
                self.send_append_entries(entry)
                return raft_pb2.ServeClientReply(
                    data="", leaderID=str(self.node_id), success=True
                )
            else:
                self.dump_file.write(
                    f"Node {self.node_id} received a SET {key} {value} request but is not the leader.\n"
                )
                self.dump_file.flush()
                return raft_pb2.ServeClientReply(
                    data="", leaderID=str(self.leader_id), success=False
                )

    def get_value(self, key):
        # for entry in reversed(self.log):
        #     operation, entry_key, value, _ = entry
        #     if operation == "SET" and entry_key == key:
        #         return value

        self.log_file.seek(0)
        for line in reversed(list(self.log_file)):
            entry = line.strip().split()
            if entry[0] == "SET" and entry[1] == key:
                return entry[2]
        return ""

    def AppendEntries(self, request, context):
        self.restart_election_timer()
        if self.state == "FOLLOWER" and self.current_term <= request.term:
            self.current_term = request.term
            self.voted_for = None
            self.leader_id = request.leaderID
            self.persist_metadata()

            prev_log_index = request.prevLogIndex
            prev_log_term = request.prevLogTerm
            entries = request.entries
            # print(f"Entry: {entry}")

            if len(self.log) <= prev_log_index:
                self.log = self.log[:prev_log_index]

            if (
                len(self.log) > prev_log_index
                and self.log[prev_log_index][3] != prev_log_term
            ):
                self.log = self.log[:prev_log_index]
            # if entry:
            #     self.log.append((entry.operation, entry.key, entry.value, entry.term))
            #     self.persist_log(entry)

            # if len(self.log) > prev_log_index:
            #     self.log = self.log[:prev_log_index + 1]
            # if len(self.log) <= prev_log_index:
            #     self.log = self.log[:prev_log_index]

            # elif self.log[prev_log_index][3] != prev_log_term:
            #     self.log = self.log[:prev_log_index]
            for entry in entries:
                if entry.operation != "SET" and self.log and self.log[-1] == (entry.operation, entry.key, entry.value, entry.term):
                    continue
                self.log.append((entry.operation, entry.key, entry.value, entry.term))
                self.persist_log(entry)

            # self.log.append((entry.operation, entry.key, entry.value, entry.term))
            # self.persist_log(entry)

            if request.leaderCommit > self.commit_length:
                self.commit_length = min(request.leaderCommit, len(self.log))
                for i in range(
                    self.commit_length - len(request.entries), self.commit_length
                ):

                    entry = self.log[i]
                    self.dump_file.write(
                        f"Node {self.node_id} (follower) committed the entry "
                        f"{entry[0]} {entry[1]} {entry[2]} to the state machine.\n"
                    )
                    self.dump_file.flush()
                    self.commit_entry(entry, log=True)

                # self.dump_file.write(
                #     f"Node {self.node_id} (follower) committed the entry "
                #     f"{entry.operation} {entry.key} {entry.value} to the state machine.\n"
                # )
                # self.dump_file.flush()

            if self.state == "FOLLOWER" and self.current_term <= request.term:
                self.match_index[self.node_id] = prev_log_index + len(entries)

            return raft_pb2.AppendEntriesReply(term=self.current_term, success=True)
        else:
            return raft_pb2.AppendEntriesReply(term=self.current_term, success=False)

    def RequestVote(self, request, context):
        candidate_id = request.candidateID
        candidate_term = request.term
        candidate_last_log_index = request.lastLogIndex
        candidate_last_log_term = request.lastLogTerm

        # print(f"Candidate ID: {candidate_id}, Candidate term: {candidate_term}")
        # print(f"Candidate last log index: {candidate_last_log_index}, Candidate last log term: {candidate_last_log_term}")

        if candidate_term <= self.current_term:
            self.dump_file.write(
                f"Vote denied for Node {candidate_id} in term {candidate_term} by Node {self.node_id}.\n"
            )
            self.dump_file.flush()
            return raft_pb2.RequestVoteReply(
                term=self.current_term,
                voteGranted=False,
                oldLeaderLeaseDuration=self.old_leader_lease_end_time - time.time(),
            )
        else:
            self.current_term = candidate_term
            self.voted_for = None
            self.persist_metadata()

        if self.state == "FOLLOWER":
            self.restart_election_timer()

        # if self.current_term <= candidate_term:
        # if self.log:
        #     last_log_term = self.log[-1][3]
        # else:
        #     last_log_term = 0
        last_log_term = self.log[-1][3] if self.log else 0

        log_ok = (candidate_last_log_term > last_log_term) or (
            candidate_last_log_term == last_log_term
            and candidate_last_log_index >= len(self.log)
        )

        if (self.voted_for is None or self.voted_for == candidate_id) and log_ok:
            self.current_term = candidate_term
            self.voted_for = candidate_id
            self.persist_metadata()
            self.dump_file.write(
                f"Vote granted for Node {candidate_id} in term {candidate_term} by Node {self.node_id}.\n"
            )
            self.dump_file.flush()
            return raft_pb2.RequestVoteReply(
                term=self.current_term,
                voteGranted=True,
                oldLeaderLeaseDuration=self.old_leader_lease_end_time - time.time(),
            )

        self.dump_file.write(
            f"Vote denied for Node {candidate_id} in term {candidate_term} by Node {self.node_id}.\n"
        )
        self.dump_file.flush()
        return raft_pb2.RequestVoteReply(
            term=self.current_term,
            voteGranted=False,
            oldLeaderLeaseDuration=self.old_leader_lease_end_time - time.time(),
        )

    def step_down(self):
        self.dump_file.write(f"Node {self.node_id} Stepping down\n")
        self.dump_file.flush()
        self.state = "FOLLOWER"
        self.leader_id = None
        self.voted_for = None
        self.lease_acquired = False
        self.persist_metadata()
        self.restart_election_timer()

    def renew_lease(self):
        if self.state == "LEADER" and self.lease_acquired:
            if time.time() > self.lease_start_time + self.lease_timeout:
                self.dump_file.write(
                    f"Leader {self.node_id} lease renewal failed. Stepping Down.\n"
                )
                self.dump_file.flush()
                self.step_down()
            else:
                self.lease_start_time = time.time()
                self.old_leader_lease_end_time = (
                    self.lease_start_time + self.lease_timeout
                )
                self.restart_lease_renewal_timer()


if __name__ == "__main__":
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_node_instance = RaftNode(4, 5)
        raft_pb2_grpc.add_RaftNodeServicer_to_server(raft_node_instance, server)
        server.add_insecure_port("[::]:50055")
        server.start()
        print(f"Raft node 4 started on port 50055")
        server.wait_for_termination()

    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop(None)