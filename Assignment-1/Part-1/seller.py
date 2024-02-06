import grpc
import market_pb2
import market_pb2_grpc
import uuid

seller_uuid = uuid.uuid1()
items = {}


def register_seller():
    channel = grpc.insecure_channel("localhost:50051")
    stub = market_pb2_grpc.MarketServiceStub(channel)
    seller_info = market_pb2.SellerInfo(
        address="192.13.188.178:50051", uuid=str(seller_uuid)
    )
    request = market_pb2.RegisterSellerRequest(seller_info=seller_info)
    response = stub.RegisterSeller(request)
    if response.status == market_pb2.RegisterSellerResponse.Status.SUCCESS:
        print("SUCCESS\n")
    else:
        print("SELLER ALREADY EXISTS\n")


def sell_item():
    channel = grpc.insecure_channel("localhost:50051")
    stub = market_pb2_grpc.MarketServiceStub(channel)
    seller_info = market_pb2.SellerInfo(
        address="192.13.188.178:50051", uuid=str(seller_uuid)
    )
    product_name = "iPhone 15"
    item_details = market_pb2.ItemDetails(
        product_name=product_name,
        category=market_pb2.ItemDetails.Category.electronics,
        quantity=10,
        description="This is a phone",
        seller_address="192.13.188.178:50051",
        price_per_unit=10_000.0,
        rating=0.0,
    )
    request = market_pb2.SellItemRequest(
        seller_info=seller_info, item_details=item_details
    )
    response = stub.SellItem(request)
    if response.status == market_pb2.SellItemResponse.Status.SUCCESS:
        print("SUCCESS")
        print(f"Item ID: {response.item_id}\n")
        items[response.item_id] = product_name
    else:
        print("INVALID SELLER\n")


def update_item(new_item_id, new_quantity, new_price_per_unit):
    channel = grpc.insecure_channel("localhost:50051")
    stub = market_pb2_grpc.MarketServiceStub(channel)
    seller_info = market_pb2.SellerInfo(
        address="192.13.188.178:50051", uuid=str(seller_uuid)
    )
    request = market_pb2.UpdateItemRequest(
        seller_info=seller_info,
        item_id=new_item_id,
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


def delete_item(item_id):
    channel = grpc.insecure_channel("localhost:50051")
    stub = market_pb2_grpc.MarketServiceStub(channel)
    seller_info = market_pb2.SellerInfo(
        address="192.13.188.178:50051", uuid=str(seller_uuid)
    )
    request = market_pb2.DeleteItemRequest(seller_info=seller_info, item_id=item_id)
    response = stub.DeleteItem(request)
    if response.status == market_pb2.UpdateItemResponse.Status.INVALID_SELLER:
        print("INVALID_SELLER\n")
    elif response.status == market_pb2.UpdateItemResponse.Status.INVALID_ITEM_ID:
        print("INVALID_ITEM_ID\n")
    else:
        print("SUCCESS\n")


def display_seller_items():
    channel = grpc.insecure_channel("localhost:50051")
    stub = market_pb2_grpc.MarketServiceStub(channel)
    seller_info = market_pb2.SellerInfo(
        address="192.13.188.178:50051", uuid=str(seller_uuid)
    )
    request = market_pb2.DisplaySellerItemsRequest(seller_info=seller_info)
    response = stub.DisplaySellerItems(request)
    if response.status == market_pb2.DisplaySellerItemsResponse.Status.SUCCESS:
        for item in response.items:
            print(
                f"Item ID: {item.item_id}, Price: ${item.price_per_unit}, Name: {item.product_name}, Category: {get_category_string(item.category)}"
            )
            print(f"Description: {item.description}")
            print(f"Quantity Remaining: {item.quantity}")
            print(f"Seller: {item.seller_address}")
            print(f"Rating: {item.rating} / 5")
            print()
    else:
        print("NO_ITEMS_FOUND\n")

def get_category_string(category_num):
    category_map = {
        0: "electronics",
        1: "fashion",
        2: "others",
        3: "any"
    }
    return category_map[category_num]


if __name__ == "__main__":

    while True:
        print("1. Register Seller")
        print("2. Sell Item")
        print("3. Update Item")
        print("4. Delete Item")
        print("5. Display Seller Items")
        print("6. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            register_seller()
        elif choice == "2":
            sell_item()
        elif choice == "3":
            item_id = input("Enter the item ID: ")
            new_quantity = int(input("Enter the new quantity: "))
            new_price_per_unit = float(input("Enter the new price per unit: "))
            update_item(item_id, new_quantity, new_price_per_unit)
        elif choice == "4":
            item_id = input("Enter the item ID: ")
            delete_item(item_id)
        elif choice == "5":
            display_seller_items()
        elif choice == "6":
            break
        else:
            print("Invalid choice")
            continue
