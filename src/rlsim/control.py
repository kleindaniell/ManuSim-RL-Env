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
            ("finished", np.bool),  # If order is finished
            ("finish_at", np.float64),  # Finished at
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
        ]
        do_orders = np.zeros(size, dtype=do_dtype)
        do_orders["id"] = range(0, len(do_orders))

        return do_orders

    def add_po(
        self,
        product: str,
        quantity: np.int16 = 1,
        due_date: np.float64 = 0,
        scheduled: np.float64 = 0,
        released: np.float64 = 0,
        priority: np.int8 = 0,
        process_total: np.int16 = 0,
        process_actual: np.int16 = 0,
        finished: np.bool = 0,
        finish_time: np.float64 = 0,
    ):

        next_id = self.po[self.po["used"] == False]["id"][0]

        po_order = (
            next_id,
            product,
            quantity,
            due_date,
            scheduled,
            released,
            priority,
            process_total,
            process_actual,
            finished,
            finish_time,
        )

        self.po[self.po["id"] == next_id] = po_order

        return next_id

    def add_do(
        self,
        id: np.int32,
        used: np.bool,
        product: "U12",
        quantity: np.int16,
        due_date: np.float64,
        arrived_at: np.float64,
        delivered_at: np.float64,
        delivered: np.bool,
    ):
        next_id = self.po[self.po["used"] == False]["id"][0]

        po_order = (
            next_id,
            product,
            quantity,
            due_date,
            scheduled,
            released,
            priority,
            process_total,
            process_actual,
            finished,
            finish_time,
        )

        self.po[self.po["id"] == next_id] = po_order

        return next_id

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
        # Inbound
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


class ProductionOrder:
    def __init__(self):
        self.products: np.ndarray = np.array([])
        self.quantitys: np.ndarray = np.array([])
        self.schedules: np.ndarray = np.array([])
        self.releaseds: np.ndarray = np.array([])
        self.duedates: np.ndarray = np.array([])
        self.finisheds: np.ndarray = np.array([])
        self.prioritys: np.ndarray = np.array([])
        self.process_totals: np.ndarray = np.array([])
        self.process_finisheds: np.ndarray = np.array([])
        self.ids: np.ndarray = np.array([])


@dataclass
class DemandOrder:
    def __init__(self):
        self.products: np.ndarray = np.array([])
        self.quantitys: np.ndarray = np.array([])
        self.duedates: np.ndarray = np.array([])
        self.ariveds: np.ndarray = np.array([])
        self.delivereds: np.ndarray = np.array([])
        self.ids: np.ndarray = np.array([])
