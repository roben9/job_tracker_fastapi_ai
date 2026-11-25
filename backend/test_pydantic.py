# from pydantic import validate_call


# @validate_call
# def calculate_total(price: int, quantity: int):
#     total = price * quantity
#     return total


# print(calculate_total("10", 2))


from pydantic import BaseModel


class Product(BaseModel):
    product_name: str
    price: int
    in_stock: bool = True


product = Product(product_name="Keyboard", price="1500", in_stock=True)

print(product.model_dump_json())
