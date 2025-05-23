import simpy

from rlsim.control import Stores, ProductionOrder, DemandOrder
from rlsim.monitor import Monitor
from rlsim.scheduler import Scheduler


class ArticleScheduler(Scheduler):
    def __init__(self, store, interval, constraint_resource: str):
        super().__init__(store, interval)
        self.constraint_resource = constraint_resource

    def run_scheduler(self):

        for product in self.stores.products.keys():
            self.env.process(self._scheduler(product, self.interval))

    def _scheduler(self, product, interval):

        while True:

            demandOrder: DemandOrder = yield self.stores.demand_orders[product].get()

            quantity = demandOrder.quantity
            productionOrder = ProductionOrder(product=product, quantity=quantity)

            if production_order["constraint"]:
                duedate = demandOrder.duedate
                constraint_time = self.products_config[product].get(
                    "constraint_time", 0
                )
                schedule = (
                    duedate
                    - self.shipping_buffer[product]
                    - constraint_time
                    - self.constraint_buffer
                )
                production_order["schedule"] = schedule

            else:
                production_order["schedule"] = self.env.now
                production_order["priority"] = 0

            self.env.process(self.releasePO(production_order))
