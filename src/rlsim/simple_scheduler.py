# from rlsim.control import ProductionOrder, DemandOrder
from rlsim.scheduler import Scheduler


class SimpleScheduler(Scheduler):
    def __init__(self, store, interval):
        super().__init__(store, interval)
        self.run_scheduler()

    # def _scheduler(self):
    #     while True:
    #         for product in self.stores.products.keys():
    #             productionOrder = ProductionOrder(product=product, quantity=1)
    #             self.env.process(self.release_order(productionOrder))

    #         yield self.env.timeout(self.interval)

    def _scheduler(self, product):

        while True:

            demandOrderId = yield self.stores.inbound_demand_orders[product].get()
            demandOrder = self.stores.do[self.stores.do["id"]==demandOrderId]
            demandQuantity = demandOrder["quantity"]

            productionOrder = self.stores.create_po(
                product=product,
                quantity=demandQuantity,
                scheduled=self.env.now,
                priority=0
            )

            self.env.process(self.release_order(productionOrder))
            
            yield self.stores.outbound_demand_orders[product].put(demandOrderId)

    def run_scheduler(self):

        for product in self.stores.products.keys():
            self.env.process(self._scheduler(product))
