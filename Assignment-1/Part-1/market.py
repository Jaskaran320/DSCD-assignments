import grpc
from concurrent import futures
import market_pb2
import market_pb2_grpc
import uuid


class MarketServicer(market_pb2_grpc.MarketServiceServicer):

    def __init__(self):
        self.sellers = {}
        self.items = {}
        self.ratings = {}
        self.wishlist = {}

    def RegisterSeller(self, request, context):
        seller_info = request.seller_info
        print(f"Seller join request from {seller_info.address}, uuid = {seller_info.uuid}")

        if seller_info.uuid in self.sellers:
            response = market_pb2.RegisterSellerResponse()
            response.status = market_pb2.RegisterSellerResponse.Status.FAILED
            return response

        self.sellers[seller_info.uuid] = seller_info.address
        response = market_pb2.RegisterSellerResponse()
        response.status = market_pb2.RegisterSellerResponse.Status.SUCCESS

        return response

    def SellItem(self, request, context):
        seller_info = request.seller_info
        item_details = request.item_details
        print(f"Sell Item request from {seller_info.address}")

        item_id = str(uuid.uuid4())

        self.items[item_id] = {
            "product_name": item_details.product_name,
            "category": item_details.WhichOneof("Category"),
            "quantity": item_details.quantity,
            "description": item_details.description,
            "seller_address": item_details.seller_address,
            "price_per_unit": item_details.price_per_unit,
            "rating": [],
        }

        response = market_pb2.SellItemResponse()
        response.item_id = item_id
        response.status = market_pb2.SellItemResponse.Status.SUCCESS

        return response

    def UpdateItem(self, request, context):
        seller_info = request.seller_info
        item_id = request.item_id
        new_quantity = request.new_quantity
        new_price_per_unit = request.new_price_per_unit
        print(f"Update Item {item_id} request from {seller_info.address}")

        if (seller_info.uuid not in self.sellers
            or self.sellers[seller_info.uuid]["address"] != seller_info.address):
            response = market_pb2.UpdateItemResponse()
            response.status = market_pb2.UpdateItemResponse.Status.INVALID_SELLER
            return response

        if item_id not in self.items:
            response = market_pb2.UpdateItemResponse()
            response.status = market_pb2.UpdateItemResponse.Status.FAILED
            return response

        self.items[item_id]["quantity"] = new_quantity
        self.items[item_id]["price_per_unit"] = new_price_per_unit

        ########################
        # TODO: send notification to all buyers who have added this item to their wishlist
        ########################

        response = market_pb2.UpdateItemResponse()
        response.status = market_pb2.UpdateItemResponse.Status.SUCCESS
        # self.notify_buyer(item_id)

        return response

    def DeleteItem(self, request, context):
        seller_info = request.seller_info
        item_id = request.item_id
        print(f"Delete Item {item_id} request from {seller_info.address}")

        if (seller_info.uuid not in self.sellers 
        or self.sellers[seller_info.uuid]["address"] != seller_info.address):
            response = market_pb2.DeleteItemResponse()
            response.status = market_pb2.DeleteItemResponse.Status.INVALID_SELLER
            return response

        if item_id not in self.items:
            response = market_pb2.DeleteItemResponse()
            response.status = market_pb2.DeleteItemResponse.Status.INVALID_ITEM_ID
            return response

        del self.items[item_id]
        response = market_pb2.DeleteItemResponse()
        response.status = market_pb2.DeleteItemResponse.Status.SUCCESS

        return response

    def DisplaySellerItems(self, request, context):
        seller_info = request.seller_info
        print(f"Display Items request from {seller_info.address}")
        
        seller_items = []
        for item_id, item_details in self.items.items():
            if item_details["seller_address"] == seller_info.address:
                item = market_pb2.DisplaySellerItemsResponse.Item(
                    item_id=item_id,
                    price=item_details["price_per_unit"],
                    product_name=item_details["product_name"],
                    category=market_pb2.Category.Value(item_details["category"]), # TODO: check this
                    description=item_details["description"],
                    quantity_remaining=item_details["quantity"],
                    seller_address=item_details["seller_address"],
                    rating=item_details["rating"]
                )
                seller_items.append(item)

        if len(seller_items) == 0:
            response = market_pb2.DisplaySellerItemsResponse()
            response.status = market_pb2.DisplaySellerItemsResponse.Status.NO_ITEMS
            return response

        response = market_pb2.DisplaySellerItemsResponse()
        response.status = market_pb2.DisplaySellerItemsResponse.Status.SUCCESS
        response.items.extend(seller_items)

        return response

    def SearchItem(self, request, context):
        item_name = request.item_name
        category = request.category
        print(f"Search request for Item name: {item_name if item_name else '[ALL_ITEMS]'}, Category: {category}")

        matched_items = []
        for _, item_details in self.items.items():
            if (not item_name or item_details["product_name"].lower() == item_name.lower()) and \
               (category == market_pb2.category.any or item_details["category"] == category.name):
                matched_item = market_pb2.ItemDetails(
                    product_name=item_details["product_name"],
                    # category=market_pb2.category.Value(item_details["category"]),
                    category=item_details["category"],
                    quantity=item_details["quantity"],
                    description=item_details["description"],
                    seller_address=item_details["seller_address"],
                    price_per_unit=item_details["price_per_unit"],
                    rating=item_details["rating"]
                )
                matched_items.append(matched_item)

        response = market_pb2.SearchItemResponse()
        response.items.extend(matched_items)

        return response

    def BuyItem(self, request, context):
        item_id = request.item_id
        quantity = request.quantity
        buyer_address = request.buyer_address
        print(f"Buy request {quantity} of item {item_id}, from {buyer_address}")

        if item_id in self.items and self.items[item_id]["quantity"] >= quantity:
            self.items[item_id]["quantity"] -= quantity
            response = market_pb2.BuyItemResponse()
            response.status = market_pb2.BuyItemResponse.Status.SUCCESS
        else:
            response = market_pb2.BuyItemResponse()
            response.status = market_pb2.BuyItemResponse.Status.FAILED

        return response

    def AddToWishList(self, request, context):
        item_id = request.item_id
        buyer_address = request.buyer_address
        print(f"Wishlist request of item {item_id}, from {buyer_address}")

        if buyer_address in self.wishlist:
            self.wishlist[buyer_address].append(item_id)
        else:
            self.wishlist[buyer_address] = [item_id]

        response = market_pb2.AddToWishListResponse()
        response.status = market_pb2.AddToWishListResponse.Status.SUCCESS
        return response

    def RateItem(self, request, context):
        item_id = request.item_id
        buyer_address = request.buyer_address
        rating = request.rating
        print(f"{buyer_address} rated item {item_id} with {rating} stars")

        if item_id not in self.items:
            response = market_pb2.RateItemResponse()
            response.status = market_pb2.RateItemResponse.Status.ITEM_NOT_FOUND

        if item_id in self.ratings and buyer_address in self.ratings[item_id]:
            response = market_pb2.RateItemResponse()
            response.status = market_pb2.RateItemResponse.Status.ALREADY_RATED

        current_rating = self.items[item_id]["rating"]
        num_ratings = len(self.ratings.get(item_id, []))
        new_rating = (current_rating * num_ratings + rating) / (num_ratings + 1)
        self.items[item_id]["rating"] = new_rating

        if item_id in self.ratings:
            self.ratings[item_id].append(buyer_address)
        else:
            self.ratings[item_id] = [buyer_address]

        response = market_pb2.RateItemResponse()
        response.status = market_pb2.RateItemResponse.Status.SUCCESS

        return response
    
    def notify_buyer(self, item_id):
        channel = grpc.insecure_channel('localhost:50051')
        stub = market_pb2_grpc.MarketServiceStub(channel)
        for buyer_address in self.wishlist:
            if item_id in self.wishlist[buyer_address]:
                item_details = self.items[item_id]
                request = market_pb2.NotifyBuyerRequest(
                    item_id=item_id,
                    item_details=market_pb2.ItemDetails(
                        product_name=item_details["product_name"],
                        category=market_pb2.Category.Value(item_details["category"]),
                        quantity=item_details["quantity"],
                        description=item_details["description"],
                        seller_address=item_details["seller_address"],
                        price_per_unit=item_details["price_per_unit"],
                        rating=item_details["rating"]
                    )
                )
                response = stub.NotifyBuyer(request)
                if response.status == market_pb2.NotifyBuyerResponse.Status.SUCCESS:
                    print(f"Notification sent to buyer {buyer_address}")
                else:
                    print(f"Notification failed for buyer {buyer_address}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    market_pb2_grpc.add_MarketServiceServicer_to_server(MarketServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
