from dataclasses import dataclass, field
from typing import Optional

import simpy
import numpy as np


class Stores:
    def __init__(
        self,
        env: simpy.Environment,
        resources: dict,
        products: dict,
    ):
        self.env = env
        self.resources = resources
        self.products = products

        self._create_process_data()
        self._create_resources_stores()
        self._create_products_stores()

        self.po = self._create_production_orders()
        self.do = self._create_demand_orders()

    def _create_production_orders(self, size=100000):
        po_dtype = [
            ("id", np.int32),  # Order ID
            ("used", np.bool),  # If slod is used
            ("product", "U12"),  # Product name
            ("quantity", np.int16),  # Product quantity
            ("due_date", np.float64),  # Due date
            ("scheduled", np.float64),  # Scheduled to release
            ("released", np.float64),  # Released time to shopfloor
            ("priority", np.int8),  # Order priority
            ("process_total", np.int16),  # Total process that order needs
            ("process_actual", np.int16),  # Actual process that order is
            ("finish_at", np.float64),  # Finished at
            ("status", str),  # If order is finished
            ("resource", str),  # Orders actual resource
        ]
        po_orders = np.zeros(size, dtype=po_dtype)
        po_orders["id"] = range(0, len(po_orders))
        return po_orders

    def _create_demand_orders(self, size=100000):
        do_dtype = [
            ("id", np.int32),  # Order ID
            ("used", np.bool),  # If slod is used
            ("product", "U12"),  # Product name
            ("quantity", np.int16),  # Product quantity
            ("due_date", np.float64),  # Due date
            ("arrived_at", np.float64),  # Arrived at
            ("delivered_at", np.float64),  # Delivered at
            ("delivered", np.bool),  # If order is delivered
            ("processed", np.bool),  # If order is processed by scheduler
        ]
        do_orders = np.zeros(size, dtype=do_dtype)
        do_orders["id"] = range(0, len(do_orders))

        return do_orders

    def create_po(
        self,
        product: str,
        quantity: np.int16 = 1,
        due_date: np.float64 = 0,
        scheduled: np.float64 = 0,
        released: np.float64 = 0,
        priority: np.int8 = 0,
        process_total: np.int16 = 0,
        process_actual: np.int16 = 0,
        finish_at: np.float64 = 0,
    ):
        mask = self.po["used"].__invert__()
        if any(mask):
            po = self.po[mask][0]
        else:
            # Sanitize orders
            pass

        po_id = po["id"]
        po["product"] = product
        po["quantity"] = quantity
        po["due_date"] = due_date
        po["scheduled"] = scheduled
        po["released"] = released
        po["priority"] = priority
        po["process_total"] = process_total
        po["process_actual"] = process_actual
        po["finish_at"] = finish_at

        self.po[self.po["id"] == po_id] = po

        return po

    def create_do(
        self,
        product: str,
        quantity: np.int16 = 1,
        due_date: np.float64 = 0,
        arrived_at: np.float64 = 0,
        delivered_at: np.float64 = 0,
        delivered: np.int8 = 0,
        processed: np.bool = False,
    ):
        mask = self.do["used"].__invert__()
        if any(mask):
            do = self.do[mask][0]
        else:
            # Sanitize orders
            pass

        do_id = do["id"]
        do["product"] = product
        do["quantity"] = quantity
        do["due_date"] = due_date
        do["arrived_at"] = arrived_at
        do["delivered_at"] = delivered_at
        do["delivered"] = delivered
        do["processed"] = processed

        self.do[self.do["id"] == do_id] = do

        return do

    def _create_process_data(self) -> None:
        self.processes_name_list = {}
        self.processes_value_list = {}
        self.processes = {}

        for product in self.products:
            processes = self.products[product].get("processes")
            self.processes_name_list[product] = list(processes.keys())
            self.processes_value_list[product] = list(processes.values())

    def _create_resources_stores(self) -> None:
        self.resource_output = {}
        self.resource_input = {}
        self.resource_processing = {}
        self.resource_transport = {}
        self.resource_utilization = {}
        self.resource_breakdowns = {}

        for resource in self.resources:
            self.resource_output[resource] = simpy.FilterStore(self.env)
            self.resource_input[resource] = simpy.FilterStore(self.env)
            self.resource_processing[resource] = simpy.Store(self.env)
            self.resource_transport[resource] = simpy.Store(self.env)
            self.resource_utilization[resource] = 0
            self.resource_breakdowns[resource] = []

    def _create_products_stores(self) -> None:
        # Outbound
        self.finished_orders = {}
        self.finished_goods = {}
        # Demand orders
        self.inbound_demand_orders = {}
        self.outbound_demand_orders = {}
        # KPIs
        self.delivered_ontime = {}
        self.delivered_late = {}
        self.lost_sales = {}
        self.wip = {}
        self.total_wip = simpy.Container
        for product in self.products:
            self.finished_orders[product] = simpy.FilterStore(self.env)
            self.finished_goods[product] = simpy.Container(self.env)
            self.inbound_demand_orders[product] = simpy.FilterStore(self.env)
            self.outbound_demand_orders[product] = simpy.FilterStore(self.env)
            self.delivered_ontime[product] = simpy.Container(self.env)
            self.delivered_late[product] = simpy.Container(self.env)
            self.lost_sales[product] = simpy.Container(self.env)
            self.wip[product] = simpy.Container(self.env)


@dataclass
class DemandOrder:
    def __init__(self):
        self.products: np.ndarray = np.array([])
        self.quantitys: np.ndarray = np.array([])
        self.duedates: np.ndarray = np.array([])
        self.ariveds: np.ndarray = np.array([])
        self.delivereds: np.ndarray = np.array([])
        self.ids: np.ndarray = np.array([])


@dataclass
class ProductionOrder(np.ndarray):
    _id_counter = 0

    def __new__(
        cls,
        product: str,
        quantity: np.int16 = 1,
        due_date: np.float32 = 0,
        scheduled: np.float32 = 0,
        released: np.float32 = 0,
        priority: np.int8 = 9,
        process_total: np.int16 = 0,
        process_actual: np.int16 = 0,
        finished: np.bool = False,
        finish_at: np.float32 = 0,
        local: str = "backlog",
        id: np.int32 = None,
    ):
        if id is None:
            id = cls._id_counter
            cls._id_counter += 1

        po_dtype = np.dtype(
            [
                ("id", np.int32),  # Order ID
                ("product", "U50"),  # Product name
                ("quantity", np.int16),  # Product quantity
                ("due_date", np.float32),  # Due date
                ("scheduled", np.float32),  # Scheduled to release
                ("released", np.float32),  # Released time to shopfloor
                ("priority", np.int8),  # Order priority
                ("process_total", np.int16),  # Total process that order needs
                ("process_finished", np.int16),  # Actual process that order is
                ("finished", np.bool),  # If order is finished
                ("finish_at", np.float32),  # Finished at
                ("status", "U50"),  # Local on the production line
            ]
        )

        raw_data = (
            id,
            product,
            quantity,
            due_date,
            scheduled,
            released,
            priority,
            process_total,
            process_actual,
            finished,
            finish_at,
            local,
        )

        arr = np.array([raw_data], dtype=po_dtype)[0]

        return arr.view(cls)

    @classmethod
    def reset_counter(cls, value=0):
        cls._id_counter = value
