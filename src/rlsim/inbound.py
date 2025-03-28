import simpy
from rlsim.control import Stores
from rlsim.utils import random_number


class Inbound:
    def __init__(
        self,
        stores: Stores,
        products_cfg: dict,
    ):
        self.order_id = 0

        self.stores = stores
        self.env: simpy.Environment = stores.env
        self.products = products_cfg

        for product in self.products.keys():
            self.env.process(self._generate_orders(product))

    def _generate_orders(self, product):
        product_config = self.products[product]

        freq_dist = product_config["demand"]["freq"].get("dist")
        freq_params = product_config["demand"]["freq"].get("params")
        quantity_dist = product_config["demand"]["quantity"].get("dist")
        quantity_params = product_config["demand"]["quantity"].get("params")
        due_dist = product_config["demand"]["duedate"].get("dist")
        due_params = product_config["demand"]["duedate"].get("params")

        while True:
            frequency = random_number(freq_dist, freq_params)
            quantity = round(random_number(quantity_dist, quantity_params), 0)
            duedate = random_number(due_dist, due_params)

            yield self.env.timeout(frequency)

            duedate += self.env.now
            now = self.env.now

            order = {
                "id": self.order_id,
                "product": product,
                "quantity": quantity,
                "arived": now,
                "duedate": duedate,
                "delivered": -1,
            }

            yield self.stores.demand_orders[product].put(order)
            yield self.stores.demand_orders[product].put(order)
            # yield self.actual_demand[product].put(demand["quantity"])
            self.order_id += 1
