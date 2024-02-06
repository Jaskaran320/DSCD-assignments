import grpc
import market_pb2
import market_pb2_grpc

def search_item(item_name, category):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.SearchItemRequest(item_name=item_name, category=category)
    response = stub.SearchItem(request)
    for item in response.items:
        print(f"Item ID: {item.item_id}, Price: ${item.price_per_unit}, Name: {item.product_name}, Category: {get_category_string(item.category)}")
        print(f"Description: {item.description}")
        print(f"Quantity Remaining: {item.quantity}")
        print(f"Rating: {item.rating} / 5  |  Seller: {item.seller_address}\n")

def buy_item(item_id, quantity, buyer_address):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.BuyItemRequest(item_id=item_id, quantity=quantity, buyer_address=buyer_address)
    response = stub.BuyItem(request)
    if response.status == market_pb2.BuyItemResponse.QUANTITY_EXCEEDS_STOCK:
        print("QUANTITY EXCEEDS STOCK\n")
    elif response.status == market_pb2.BuyItemResponse.ITEM_NOT_FOUND:
        print("INVALID ITEM ID\n")
    else:
        print("SUCCESS\n")

def add_to_wishlist(item_id, buyer_address):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.AddToWishListRequest(item_id=item_id, buyer_address=buyer_address)
    response = stub.AddToWishList(request)
    if response.status == market_pb2.AddToWishListResponse.SUCCESS:
        print("SUCCESS\n")
    elif response.status == market_pb2.AddToWishListResponse.ITEM_ALREADY_IN_WISHLIST:
        print("ITEM ALREADY IN WISHLIST\n")

def rate_item(item_id, buyer_address, rating):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.RateItemRequest(item_id=item_id, buyer_address=buyer_address, rating=rating)
    response = stub.RateItem(request)
    if response.status == market_pb2.RateItemResponse.ITEM_NOT_FOUND:
        print("INVALID ITEM ID\n")
    elif response.status == market_pb2.RateItemResponse.ITEM_ALREADY_RATED:
        print("ITEM ALREADY RATED\n")
    else:
        print("SUCCESS\n")

def get_category_string(category_num):
    category_map = {
        0: "electronics",
        1: "fashion",
        2: "others",
        3: "any"
    }
    return category_map[category_num]

# def NotifyBuyer(request, context):
#     print("Notification received")
#     print(f"Item ID: {request.item_id}, Quantity: {request.quantity}, Buyer: {request.buyer_address}")
#     return market_pb2.NotifyBuyerResponse(status=market_pb2.NotifyBuyerResponse.Status.SUCCESS)

if __name__ == '__main__':
    print("Welcome to the Online Market Place")
    while True:
        print("1. Search Item")
        print("2. Buy Item")
        print("3. Add to Wishlist")
        print("4. Rate Item")
        print("5. Exit")
        choice = int(input("Enter your choice: "))
        if choice == 1:
            # ask item name and category
            item_name = input("Enter the item name (leave empty for all items): ")
            category = input("Enter the category (electronics, fashion, others, any): ")
            search_item(item_name, category)
        elif choice == 2:
            item_id = input("Enter the item ID: ")
            quantity = int(input("Enter the quantity: "))
            buyer_address = input("Enter your address: ")
            buy_item(item_id, quantity, buyer_address)
        elif choice == 3:
            item_id = input("Enter the item ID: ")
            buyer_address = input("Enter your address: ")
            add_to_wishlist(item_id, buyer_address)
        elif choice == 4:
            item_id = input("Enter the item ID: ")
            buyer_address = input("Enter your address: ")
            rating = int(input("Enter the rating: "))
            rate_item(item_id, buyer_address, rating)
        else:
            break
