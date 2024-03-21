import threading
from concurrent import futures
import grpc
import market_pb2
import market_pb2_grpc
import uuid
import signal

stop_event = threading.Event()
market_ip = "localhost:50051"


def register_seller(seller_info):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.RegisterSellerRequest(seller_info=seller_info)
    response = stub.RegisterSeller(request)
    if response.status == market_pb2.RegisterSellerResponse.Status.SUCCESS:
        print("SUCCESS\n")
    else:
        print("SELLER ALREADY EXISTS\n")


def sell_item(seller_info, item_details):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.SellItemRequest(
        seller_info=seller_info, item_details=item_details
    )
    response = stub.SellItem(request)
    if response.status == market_pb2.SellItemResponse.Status.SUCCESS:
        print("SUCCESS")
        print(f"Item ID: {response.item_id}\n")
    else:
        print("INVALID SELLER\n")


def update_item(item_id, new_quantity, new_price_per_unit, seller_info):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.UpdateItemRequest(
        seller_info=seller_info,
        item_id=item_id,
        new_quantity=new_quantity,
        new_price_per_unit=new_price_per_unit,
    )
    response = stub.UpdateItem(request)
    if response.status == market_pb2.UpdateItemResponse.Status.INVALID_SELLER:
        print("INVALID_SELLER\n")
    elif response.status == market_pb2.UpdateItemResponse.Status.INVALID_ITEM_ID:
        print("INVALID_ITEM_ID\n")
    else:
        print("SUCCESS\n")


def delete_item(item_id, seller_info):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.DeleteItemRequest(seller_info=seller_info, item_id=item_id)
    response = stub.DeleteItem(request)
    if response.status == market_pb2.UpdateItemResponse.Status.INVALID_SELLER:
        print("INVALID_SELLER\n")
    elif response.status == market_pb2.UpdateItemResponse.Status.INVALID_ITEM_ID:
        print("INVALID_ITEM_ID\n")
    else:
        print("SUCCESS\n")


def display_seller_items(seller_info):
    channel = grpc.insecure_channel(market_ip)
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.DisplaySellerItemsRequest(seller_info=seller_info)
    response = stub.DisplaySellerItems(request)
    if response.status == market_pb2.DisplaySellerItemsResponse.Status.SUCCESS:
        for item in response.items:
            print(f"Item ID: {item.item_id}, Price: ${item.price_per_unit}, "
                f"Name: {item.product_name}, Category: {get_category_string(item.category)}")
            print(f"Description: {item.description}")
            print(f"Quantity Remaining: {item.quantity}")
            print(f"Seller: {item.seller_address}")
            print(f"Rating: {item.rating} / 5")
            print()
    else:
        print("NO_ITEMS_FOUND\n")


class NotificationServicer(market_pb2_grpc.NotificationServiceServicer):

    def NotifySeller(request, context):
        print(f"Notification: Item {request.item_id}, {request.item_name}, "
            f"quantity {request.quantity} has been bought by buyer {request.buyer_address}")
        response = market_pb2.NotifySellerResponse()
        response.status = market_pb2.NotifySellerResponse.Status.SUCCESS
        return response


def get_category_string(category_num):
    category_map = {0: "electronics", 1: "fashion", 2: "others", 3: "any"}
    return category_map[category_num]


def signal_handler(signal, frame):
    stop_event.set()


def run_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    market_pb2_grpc.add_NotificationServiceServicer_to_server(NotificationServicer, server)
    server.add_insecure_port("[::]:50053")
    server.start()
    stop_event.wait()
    server.stop(0)


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    server_thread = threading.Thread(target=run_grpc_server)
    server_thread.start()

    seller_address = "localhost:50053"
    seller_uuid = uuid.uuid1()
    seller_info = market_pb2.SellerInfo(address=seller_address, uuid=str(seller_uuid))
    category_sent = {
        "electronics": market_pb2.ItemDetails.Category.electronics,
        "fashion": market_pb2.ItemDetails.Category.fashion,
        "others": market_pb2.ItemDetails.Category.others,
    }

    while True:
        print("1. Register Seller")
        print("2. Sell Item")
        print("3. Update Item")
        print("4. Delete Item")
        print("5. Display Seller Items")
        print("6. Exit")
        choice = input("Enter your choice:\n")
        if choice == "1":
            register_seller(seller_info)
        elif choice == "2":
            product_name = str(input("Enter the product name: "))
            category = str(input("Enter the category (electronics, fashion, others): "))
            if category not in ["electronics", "fashion", "others"]:
                print("Invalid category\n")
                continue
            quantity = int(input("Enter the quantity: "))
            description = str(input("Enter the description: "))
            price_per_unit = float(input("Enter the price per unit: "))
            item_details = market_pb2.ItemDetails(
                product_name=product_name,
                category=category_sent[category],
                quantity=quantity,
                description=description,
                seller_address=seller_address,
                price_per_unit=price_per_unit,
                rating=0.0,
            )
            sell_item(seller_info, item_details)
        elif choice == "3":
            item_id = input("Enter the item ID: ")
            new_quantity = int(input("Enter the new quantity: "))
            new_price_per_unit = float(input("Enter the new price per unit: "))
            update_item(item_id, new_quantity, new_price_per_unit, seller_info)
        elif choice == "4":
            item_id = input("Enter the item ID: ")
            delete_item(item_id, seller_info)
        elif choice == "5":
            display_seller_items(seller_info)
        elif choice == "6":
            stop_event.set()
            break
        else:
            print("Invalid choice\n")
            continue

    server_thread.join()
