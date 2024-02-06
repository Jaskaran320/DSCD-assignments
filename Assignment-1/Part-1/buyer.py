import grpc
import market_pb2
import market_pb2_grpc

def search_item():
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    item_name = ""  # Empty to display all items
    category = market_pb2.Category.ANY  # Use ANY to display items with all categories
    request = market_pb2.SearchItemRequest(item_name=item_name, category=category)
    response = stub.SearchItem(request)
    for item in response.items:
        print(f"Item ID: {item.item_id}, Price: ${item.price}, Name: {item.product_name}, Category: {item.category},")
        print(f"Description: {item.description}")
        print(f"Quantity Remaining: {item.quantity_remaining}")
        print(f"Rating: {item.rating} / 5  |  Seller: {item.seller_address}\n")

def buy_item(item_id, quantity, buyer_address):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.BuyItemRequest(item_id=item_id, quantity=quantity, buyer_address=buyer_address)
    response = stub.BuyItem(request)
    if response.status == market_pb2.BuyItemResponse.SUCCESS:
        print("SUCCESS")
    else:
        print("FAIL")

def add_to_wishlist(item_id, buyer_address):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.AddToWishListRequest(item_id=item_id, buyer_address=buyer_address)
    response = stub.AddToWishList(request)
    if response.status == market_pb2.AddToWishListResponse.SUCCESS:
        print("SUCCESS")
    else:
        print("FAIL")

def rate_item(item_id, buyer_address, rating):
    channel = grpc.insecure_channel('localhost:50051')
    stub = market_pb2_grpc.MarketServiceStub(channel)
    request = market_pb2.RateItemRequest(item_id=item_id, buyer_address=buyer_address, rating=rating)
    response = stub.RateItem(request)
    if response.status == market_pb2.RateItemResponse.SUCCESS:
        print("SUCCESS")
    else:
        print("FAIL")

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
            search_item()
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
