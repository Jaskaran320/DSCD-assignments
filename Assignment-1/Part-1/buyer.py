import threading
from concurrent import futures
import grpc
import market_pb2
import market_pb2_grpc
import signal

stop_event = threading.Event()
market_ip = "localhost:50051"


def search_item(item_name, category):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.SearchItemRequest(item_name=item_name, category=category)
    response = stub.SearchItem(request)
    for item in response.items:
        print(
            f"Item ID: {item.item_id}, Price: ${item.price_per_unit}, Name: {item.product_name}, Category: {get_category_string(item.category)}"
        )
        print(f"Description: {item.description}")
        print(f"Quantity Remaining: {item.quantity}")
        print(f"Rating: {item.rating} / 5  |  Seller: {item.seller_address}\n")
    channel.close()


def buy_item(item_id, quantity, buyer_address):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.BuyItemRequest(
        item_id=item_id, quantity=quantity, buyer_address=buyer_address
    )
    response = stub.BuyItem(request)
    if response.status == market_pb2.BuyItemResponse.QUANTITY_EXCEEDS_STOCK:
        print("QUANTITY EXCEEDS STOCK\n")
    elif response.status == market_pb2.BuyItemResponse.ITEM_NOT_FOUND:
        print("INVALID ITEM ID\n")
    else:
        print("SUCCESS\n")
    channel.close()


def add_to_wishlist(item_id, buyer_address):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.AddToWishListRequest(
        item_id=item_id, buyer_address=buyer_address
    )
    response = stub.AddToWishList(request)
    if response.status == market_pb2.AddToWishListResponse.SUCCESS:
        print("SUCCESS\n")
    elif response.status == market_pb2.AddToWishListResponse.ITEM_ALREADY_IN_WISHLIST:
        print("ITEM ALREADY IN WISHLIST\n")
    channel.close()


def rate_item(item_id, buyer_address, rating):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.RateItemRequest(
        item_id=item_id, buyer_address=buyer_address, rating=rating
    )
    response = stub.RateItem(request)
    if response.status == market_pb2.RateItemResponse.ITEM_NOT_FOUND:
        print("INVALID ITEM ID\n")
    elif response.status == market_pb2.RateItemResponse.ITEM_ALREADY_RATED:
        print("ITEM ALREADY RATED\n")
    else:
        print("SUCCESS\n")
    channel.close()


class NotificationServicer(market_pb2_grpc.NotificationServiceServicer):

    def NotifyBuyer(request, context):
        print(f"Notification: Item {request.item_id}, {request.item_name} has been updated by the seller")
        response = market_pb2.NotifyBuyerResponse()
        response.status = market_pb2.NotifyBuyerResponse.Status.SUCCESS
        return response


def get_category_string(category_num):
    category_map = {0: "electronics", 1: "fashion", 2: "others", 3: "any"}
    return category_map[category_num]


def signal_handler(signal, frame):
    stop_event.set()


def run_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    market_pb2_grpc.add_NotificationServiceServicer_to_server(
        NotificationServicer, server
    )
    server.add_insecure_port("[::]:50053")
    server.start()
    stop_event.wait()
    server.stop(0)


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    server_thread = threading.Thread(target=run_grpc_server)
    server_thread.start()

    buyer_address = "localhost:50053"
    print("Welcome to the Online Market Place")
    
    while True:
        print("1. Search Item")
        print("2. Buy Item")
        print("3. Add to Wishlist")
        print("4. Rate Item")
        print("5. Exit")
        choice = int(input("Enter your choice:\n"))
        if choice == 1:
            item_name = input("Enter the item name (leave empty for all items): ")
            category = input("Enter the category (electronics, fashion, others, any): ")
            search_item(item_name, category)
        elif choice == 2:
            item_id = input("Enter the item ID: ")
            quantity = int(input("Enter the quantity: "))
            buy_item(item_id, quantity, buyer_address)
        elif choice == 3:
            item_id = input("Enter the item ID: ")
            add_to_wishlist(item_id, buyer_address)
        elif choice == 4:
            item_id = input("Enter the item ID: ")
            rating = int(input("Enter the rating: "))
            rate_item(item_id, buyer_address, rating)
        elif choice == 5:
            stop_event.set()
            break
        else:
            print("Invalid Choice\n")
            continue

    server_thread.join()
