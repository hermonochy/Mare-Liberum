from ..common import *


class TradeMixin:
    """Player cargo trading, port supply/demand markets and faction economies."""

    TRADE_GOODS = [
        {"id": "sugar", "name": "Raw Sugar", "base": 11, "space": 1.0, "description": "Cane sugar for refineries, taverns and the kitchens of the islands."},
        {"id": "rum", "name": "Rum", "base": 24, "space": 1.0, "description": "Casks of island rum. Popular with sailors, taverns and privateers."},
        {"id": "tobacco", "name": "Tobacco", "base": 19, "space": 1.0, "description": "Bales of cured leaf, prized by merchants and colonial factors."},
        {"id": "coffee", "name": "Coffee", "base": 31, "space": 1.0, "description": "Green coffee beans from the warmer upland plantations."},
        {"id": "cocoa", "name": "Cocoa", "base": 28, "space": 1.0, "description": "Cocoa beans and cakes for the growing chocolate trade."},
        {"id": "spices", "name": "Spices", "base": 43, "space": 0.7, "description": "Pepper, nutmeg and other costly aromatics in sealed bales."},
        {"id": "fish", "name": "Salt Fish", "base": 9, "space": 1.0, "description": "Preserved fish, a staple for ships and settlements far from fresh water."},
        {"id": "salt", "name": "Salt", "base": 10, "space": 1.0, "description": "Salt for curing food, preserving hides and provisioning fleets."},
        {"id": "timber", "name": "Ship Timber", "base": 18, "space": 1.5, "description": "Hardwood beams and planking for yards, wharves and repairs."},
        {"id": "rope", "name": "Rope & Hemp", "base": 21, "space": 1.0, "description": "Cordage for rigging, anchors, blocks and dockside work."},
        {"id": "canvas", "name": "Sailcloth", "base": 32, "space": 1.0, "description": "Heavy canvas and sailcloth for merchantmen and warships."},
        {"id": "tools", "name": "Iron Tools", "base": 45, "space": 0.9, "description": "Tools and fittings needed by shipwrights, smiths and builders."},
        {"id": "gunpowder", "name": "Gunpowder", "base": 58, "space": 0.8, "description": "Sealed powder kegs. Valuable, regulated and dangerous cargo."},
        {"id": "silver", "name": "Silver Ingots", "base": 138, "space": 0.35, "description": "Small, heavy ingots from the Spanish silver routes."},
        {"id": "contraband", "name": "Contraband", "base": 82, "space": 0.65, "description": "Unregistered luxury goods. Profitable, but not welcome in every customs house."},
    ]
    TRADE_GOODS_BY_ID = {}  # Populated immediately below the class definition.
    CARGO_CAPACITY_BY_SHIP = {
        "Sloop": 42.0,
        "Cutter": 34.0,
        "Schooner": 68.0,
        "Brigantine": 104.0,
        "Frigate": 82.0,
    }
    TRADE_QUANTITY_OPTIONS = (1, 5, "MAX")
    MARKET_TICK_SECONDS = 75.0

    FACTION_PRODUCES = {
        "British Crown": {"canvas", "tools", "gunpowder", "rum"},
        "Spanish Crown": {"silver", "sugar", "cocoa", "tobacco"},
        "French Crown": {"coffee", "spices", "canvas", "rum"},
        "Merchant League": {"fish", "salt", "rope", "timber", "sugar"},
        "Pirate Brotherhood": {"contraband", "rum", "gunpowder", "tobacco"},
        "Independent": {"fish", "salt", "timber", "rope"},
    }
    FACTION_WANTS = {
        "British Crown": {"sugar", "coffee", "cocoa", "spices", "fish"},
        "Spanish Crown": {"tools", "canvas", "gunpowder", "rope", "coffee"},
        "French Crown": {"sugar", "tobacco", "silver", "fish", "tools"},
        "Merchant League": {"silver", "spices", "coffee", "cocoa", "canvas", "gunpowder"},
        "Pirate Brotherhood": {"rum", "gunpowder", "tools", "silver", "canvas", "fish"},
        "Independent": {"tools", "canvas", "salt", "rum", "cocoa"},
    }

    def initialise_trade_economy(self):
        self.market_state = {}
        self.cargo_hold = {}
        self.cargo_average_cost = {}
        self.trade_ledger = {
            "trades": 0, "gold_spent": 0, "gold_earned": 0,
            "realised_profit": 0, "trade_volume": 0,
        }
        self.faction_economies = {
            faction: {
                "treasury": 25000,
                "prosperity": 50.0,
                "trade_balance": 0,
                "trade_volume": 0,
                "shortage_pressure": 0.0,
            }
            for faction in getattr(self, "FACTION_NAMES", ())
        }
        self.market_tick_timer = 0.0
        self.market_open = False
        self.market_selection = 0
        self.market_quantity_index = 0
        self.market_scroll = 0
        self._market_last_action = ""

        for port_index, port in enumerate(self.ports):
            # Seed each harbour independently so starting markets are stable
            # between new voyages and do not consume the campaign RNG stream.
            seed = sum((i + 1) * ord(character) for i, character in enumerate(port.name)) + port_index * 7919
            market_rng = random.Random(seed)
            produces = set(self.FACTION_PRODUCES.get(port.faction, set()))
            wants = set(self.FACTION_WANTS.get(port.faction, set()))
            name_lower = port.name.lower()
            region_lower = port.region.lower()
            if any(token in name_lower for token in ("sugar", "cane", "hook")) or "windward" in region_lower:
                produces.update({"sugar", "rum"})
            if any(token in name_lower for token in ("havana", "esperanza", "isabela", "aurelio", "escondido")) or "spanish" in region_lower:
                produces.update({"silver", "cocoa", "tobacco"})
            if any(token in name_lower for token in ("pelican", "fisher", "rest", "brigid", "lark")):
                produces.add("fish")
            if any(token in name_lower for token in ("lune", "azure", "compagnie")):
                produces.update({"canvas", "coffee", "spices"})
            if any(token in name_lower for token in ("wrecker", "gallows", "black flag", "tortuga")):
                produces.update({"contraband", "gunpowder"})
            if any(token in name_lower for token in ("timber", "reach", "haven", "sound")):
                produces.update({"timber", "rope"})

            records = {}
            for good in self.TRADE_GOODS:
                good_id = good["id"]
                target = market_rng.randint(52, 82)
                demand = market_rng.randint(34, 66)
                if good_id in wants:
                    demand += market_rng.randint(17, 28)
                if good_id in produces:
                    demand -= market_rng.randint(8, 16)
                if good_id == "contraband" and port.faction != "Pirate Brotherhood":
                    demand += market_rng.randint(4, 14)
                demand = max(12, min(96, demand))
                production = 0.12 + (market_rng.uniform(1.25, 2.45) if good_id in produces else 0.0)
                consumption = 0.18 + demand / 100.0 * market_rng.uniform(0.62, 1.05)
                stock = target * market_rng.uniform(0.58, 1.12)
                if good_id in produces:
                    stock += market_rng.uniform(10, 28)
                records[good_id] = {
                    "stock": round(max(0.0, min(150.0, stock)), 1),
                    "demand": int(demand),
                    "target": int(target),
                    "production": round(production, 2),
                    "consumption": round(consumption, 2),
                }
            self.market_state[port.name] = records
        self.refresh_faction_shortages()

    def cargo_capacity_for_ship(self, ship_name=None, upgrades=None):
        ship_name = ship_name or getattr(self, "current_ship", "Sloop")
        upgrade_values = upgrades if upgrades is not None else getattr(self, "upgrades", {})
        base = self.CARGO_CAPACITY_BY_SHIP.get(ship_name, 42.0)
        return base + max(0, int(upgrade_values.get("cargo", 0))) * 12.0

    def cargo_capacity(self):
        return self.cargo_capacity_for_ship()

    def cargo_load(self):
        total = 0.0
        for good_id, quantity in getattr(self, "cargo_hold", {}).items():
            good = self.TRADE_GOODS_BY_ID.get(good_id)
            if good:
                total += max(0, int(quantity)) * good["space"]
        return total

    def cargo_free_space(self):
        return max(0.0, self.cargo_capacity() - self.cargo_load())

    def cargo_quantity(self, good_id):
        return max(0, int(getattr(self, "cargo_hold", {}).get(good_id, 0)))

    def market_record(self, port_name, good_id):
        return self.market_state.get(port_name, {}).get(good_id)

    def market_mid_price(self, port_name, good_id):
        good = self.TRADE_GOODS_BY_ID[good_id]
        record = self.market_record(port_name, good_id)
        if not record:
            return int(good["base"])
        stock = max(0.0, float(record.get("stock", 0.0)))
        demand = max(0.0, min(100.0, float(record.get("demand", 50.0))))
        target = max(1.0, float(record.get("target", 60.0)))
        demand_factor = 0.62 + (demand / 100.0) * 0.82
        scarcity_factor = max(0.58, min(2.25, (target + 24.0) / (stock + 24.0)))
        return max(1, int(round(good["base"] * demand_factor * scarcity_factor)))

    def market_buy_price(self, port_name, good_id):
        return max(1, int(round(self.market_mid_price(port_name, good_id) * 1.06)))

    def market_sell_price(self, port_name, good_id):
        return max(1, int(round(self.market_mid_price(port_name, good_id) * 0.94)))

    def market_status(self, port_name, good_id):
        record = self.market_record(port_name, good_id) or {}
        stock = float(record.get("stock", 0.0))
        target = max(1.0, float(record.get("target", 60.0)))
        demand = int(record.get("demand", 50))
        if stock < target * 0.24:
            return "SCARCE"
        if stock > target * 1.18:
            return "PLENTIFUL"
        if demand >= 75:
            return "HIGH DEMAND"
        if demand <= 30:
            return "LOW DEMAND"
        return "STEADY"

    def open_trade_market(self):
        if not self.docked_port:
            self.toast_message("Trade is conducted at a harbour market. Make fast alongside a port first.", 3.2)
            return False
        if self.port_attitude(self.ports_by_name[self.docked_port]) == "HOSTILE":
            self.toast_message("The harbour's factors refuse to trade with a hostile captain.", 3.2)
            return False
        self.market_open = True
        self.market_selection = max(0, min(self.market_selection, len(self.TRADE_GOODS) - 1))
        self.market_quantity_index = 0
        self.toast_message(f"The factors at {self.docked_port} open their books. Compare prices before loading cargo.", 3.4)
        return True

    def close_trade_market(self):
        self.market_open = False

    def selected_trade_good(self):
        index = max(0, min(len(self.TRADE_GOODS) - 1, int(self.market_selection)))
        return self.TRADE_GOODS[index]

    def selected_trade_quantity(self):
        return self.TRADE_QUANTITY_OPTIONS[max(0, min(2, int(self.market_quantity_index)))]

    def maximum_buy_quantity(self, port_name, good_id):
        record = self.market_record(port_name, good_id) or {}
        good = self.TRADE_GOODS_BY_ID[good_id]
        stock_limit = max(0, int(float(record.get("stock", 0.0))))
        space_limit = int(self.cargo_free_space() // good["space"])
        price = self.market_buy_price(port_name, good_id)
        money_limit = max(0, int(self.gold) // price)
        return max(0, min(stock_limit, space_limit, money_limit))

    def maximum_sell_quantity(self, good_id):
        return self.cargo_quantity(good_id)

    def resolved_trade_quantity(self, action, port_name, good_id):
        requested = self.selected_trade_quantity()
        maximum = self.maximum_buy_quantity(port_name, good_id) if action == "buy" else self.maximum_sell_quantity(good_id)
        if requested == "MAX":
            return maximum
        return min(int(requested), maximum)

    def _faction_economy(self, faction):
        if faction not in self.faction_economies:
            self.faction_economies[faction] = {
                "treasury": 25000, "prosperity": 50.0, "trade_balance": 0,
                "trade_volume": 0, "shortage_pressure": 0.0,
            }
        return self.faction_economies[faction]

    def buy_trade_cargo(self, good_id, quantity=None):
        if not self.docked_port or good_id not in self.TRADE_GOODS_BY_ID:
            return 0
        port_name = self.docked_port
        good = self.TRADE_GOODS_BY_ID[good_id]
        requested = self.selected_trade_quantity() if quantity is None else quantity
        maximum = self.maximum_buy_quantity(port_name, good_id)
        quantity = maximum if requested == "MAX" else min(maximum, max(0, int(requested)))
        if quantity <= 0:
            if self.cargo_free_space() < good["space"]:
                self.toast_message("Your hold is full. Sell cargo or commission a larger hold at the shipyard.", 3.4)
            elif float(self.market_record(port_name, good_id).get("stock", 0.0)) < 1:
                self.toast_message(f"There is no {good['name'].lower()} left in the harbour warehouses.", 3.2)
            else:
                self.toast_message("You cannot afford even one unit at the current market price.", 3.0)
            return 0
        unit_price = self.market_buy_price(port_name, good_id)
        total = unit_price * quantity
        if total > self.gold:
            self.toast_message("You do not have enough gold for that purchase.", 3.0)
            return 0
        old_quantity = self.cargo_quantity(good_id)
        old_basis = float(self.cargo_average_cost.get(good_id, 0.0)) * old_quantity
        self.gold -= total
        self.cargo_hold[good_id] = old_quantity + quantity
        self.cargo_average_cost[good_id] = round((old_basis + total) / (old_quantity + quantity), 2)
        record = self.market_record(port_name, good_id)
        record["stock"] = max(0.0, round(float(record["stock"]) - quantity, 1))
        record["demand"] = min(100, int(record["demand"]) + max(1, quantity // 8))
        faction = self.ports_by_name[port_name].faction
        economy = self._faction_economy(faction)
        economy["treasury"] = int(economy.get("treasury", 0)) + int(total * 0.08)
        economy["trade_balance"] = int(economy.get("trade_balance", 0)) + total
        economy["trade_volume"] = int(economy.get("trade_volume", 0)) + total
        economy["prosperity"] = max(0.0, min(100.0, float(economy.get("prosperity", 50.0)) + quantity * 0.025))
        if record["stock"] < record["target"] * 0.25:
            economy["shortage_pressure"] = min(100.0, float(economy.get("shortage_pressure", 0.0)) + quantity * 0.12)
        self.trade_ledger["trades"] += 1
        self.trade_ledger["gold_spent"] += total
        self.trade_ledger["trade_volume"] += total
        self._market_last_action = f"Bought {quantity} {good['name']} at {port_name}."
        self.add_journal(f"Bought {quantity} units of {good['name']} at {port_name} for {total} gold ({unit_price} each).")
        self.toast_message(f"Loaded {quantity} {good['name']} for {total} gold. Hold: {self.cargo_load():.1f}/{self.cargo_capacity():.0f}.", 3.8)
        self.refresh_faction_shortages()
        return quantity

    def sell_trade_cargo(self, good_id, quantity=None):
        if not self.docked_port or good_id not in self.TRADE_GOODS_BY_ID:
            return 0
        good = self.TRADE_GOODS_BY_ID[good_id]
        requested = self.selected_trade_quantity() if quantity is None else quantity
        maximum = self.maximum_sell_quantity(good_id)
        quantity = maximum if requested == "MAX" else min(maximum, max(0, int(requested)))
        if quantity <= 0:
            self.toast_message(f"You have no {good['name'].lower()} to sell.", 2.8)
            return 0
        port_name = self.docked_port
        unit_price = self.market_sell_price(port_name, good_id)
        revenue = unit_price * quantity
        average_cost = float(self.cargo_average_cost.get(good_id, 0.0))
        realised = int(round((unit_price - average_cost) * quantity))
        self.gold += revenue
        remaining = maximum - quantity
        if remaining <= 0:
            self.cargo_hold.pop(good_id, None)
            self.cargo_average_cost.pop(good_id, None)
        else:
            self.cargo_hold[good_id] = remaining
        record = self.market_record(port_name, good_id)
        demand_before = int(record["demand"])
        record["stock"] = min(180.0, round(float(record["stock"]) + quantity, 1))
        record["demand"] = max(8, demand_before - max(1, quantity // 10))
        faction = self.ports_by_name[port_name].faction
        economy = self._faction_economy(faction)
        economy["treasury"] = max(0, int(economy.get("treasury", 0)) - int(revenue * 0.04))
        economy["trade_balance"] = int(economy.get("trade_balance", 0)) - revenue
        economy["trade_volume"] = int(economy.get("trade_volume", 0)) + revenue
        demand_factor = max(0.25, demand_before / 100.0)
        prosperity_gain = quantity * (0.045 + demand_factor * 0.11)
        economy["prosperity"] = max(0.0, min(100.0, float(economy.get("prosperity", 50.0)) + prosperity_gain))
        economy["shortage_pressure"] = max(0.0, float(economy.get("shortage_pressure", 0.0)) - quantity * demand_factor * 0.24)
        self.trade_ledger["trades"] += 1
        self.trade_ledger["gold_earned"] += revenue
        self.trade_ledger["realised_profit"] += realised
        self.trade_ledger["trade_volume"] += revenue
        self._market_last_action = f"Sold {quantity} {good['name']} at {port_name}."
        self.add_journal(f"Sold {quantity} units of {good['name']} at {port_name} for {revenue} gold ({unit_price} each); realised cargo profit {realised:+d} gold.")
        if good_id == "contraband" and faction in {"British Crown", "Spanish Crown", "French Crown"} and quantity >= 4:
            self.adjust_faction_relation(faction, -1, f"Customs officers discovered undeclared contraband at {port_name}.", announce=False)
            self.toast_message(f"Sold {quantity} contraband for {revenue} gold. Customs officers have taken an interest in your manifest.", 4.0)
        elif demand_before >= 78 and quantity >= 5:
            self.adjust_faction_relation(faction, 1, f"You supplied a scarce shipment of {good['name']} to {port_name}.", announce=False)
            self.toast_message(f"Sold {quantity} {good['name']} for {revenue} gold. The {faction} welcome the much-needed supply.", 4.2)
        else:
            self.toast_message(f"Sold {quantity} {good['name']} for {revenue} gold. Cargo result: {realised:+d} gold.", 3.8)
        self.refresh_faction_shortages()
        return quantity

    def refresh_faction_shortages(self):
        for faction in getattr(self, "FACTION_NAMES", ()):
            ports = [port for port in self.ports if port.faction == faction]
            shortages = 0
            total = 0
            for port in ports:
                for good in self.TRADE_GOODS:
                    record = self.market_record(port.name, good["id"])
                    if not record:
                        continue
                    total += 1
                    if float(record["stock"]) < float(record["target"]) * 0.28:
                        shortages += 1
            pressure = 100.0 * shortages / max(1, total)
            economy = self._faction_economy(faction)
            economy["shortage_pressure"] = round(pressure, 1)

    def update_trade_economy(self, dt):
        self.market_tick_timer += max(0.0, float(dt))
        ticks = 0
        while self.market_tick_timer >= self.MARKET_TICK_SECONDS and ticks < 4:
            self.market_tick_timer -= self.MARKET_TICK_SECONDS
            ticks += 1
            for port_name, records in self.market_state.items():
                for record in records.values():
                    stock = float(record.get("stock", 0.0))
                    stock += float(record.get("production", 0.0)) - float(record.get("consumption", 0.0))
                    record["stock"] = round(max(0.0, min(180.0, stock)), 1)
                    target = float(record.get("target", 60.0))
                    if record["stock"] < target * 0.30:
                        record["demand"] = min(100, int(record.get("demand", 50)) + 1)
                    elif record["stock"] > target * 1.25:
                        record["demand"] = max(8, int(record.get("demand", 50)) - 1)
            self.refresh_faction_shortages()
            for faction, economy in self.faction_economies.items():
                pressure = float(economy.get("shortage_pressure", 0.0))
                prosperity = float(economy.get("prosperity", 50.0))
                prosperity += (48.0 - pressure) * 0.0015
                economy["prosperity"] = round(max(0.0, min(100.0, prosperity)), 2)

    def faction_economy_summary(self, faction):
        economy = self._faction_economy(faction)
        return {
            "treasury": int(economy.get("treasury", 0)),
            "prosperity": float(economy.get("prosperity", 50.0)),
            "trade_balance": int(economy.get("trade_balance", 0)),
            "trade_volume": int(economy.get("trade_volume", 0)),
            "shortage_pressure": float(economy.get("shortage_pressure", 0.0)),
        }

    def trade_traffic_role_weights(self):
        economies = getattr(self, "faction_economies", {})
        trading = [economies.get(name, {}) for name in ("British Crown", "Spanish Crown", "French Crown", "Merchant League")]
        prosperity = sum(float(entry.get("prosperity", 50.0)) for entry in trading) / max(1, len(trading))
        shortages = sum(float(entry.get("shortage_pressure", 0.0)) for entry in trading) / max(1, len(trading))
        merchant_weight = max(16, min(58, int(round(37 + (prosperity - 50.0) * 0.34 - shortages * 0.12))))
        return [merchant_weight, 23, 14, 15, 6]

    def best_trade_routes(self, origin_port_name, limit=4):
        origin = self.ports_by_name.get(origin_port_name)
        if not origin:
            return []
        routes = []
        for good in self.TRADE_GOODS:
            good_id = good["id"]
            if float(self.market_record(origin.name, good_id).get("stock", 0.0)) < 2.0:
                continue
            buy_price = self.market_buy_price(origin.name, good_id)
            candidates = []
            for destination in self.ports:
                if destination.name == origin.name:
                    continue
                stock = float(self.market_record(destination.name, good_id).get("stock", 0.0))
                if stock > 150:
                    continue
                sell_price = self.market_sell_price(destination.name, good_id)
                distance = math.hypot(destination.x - origin.x, destination.y - origin.y)
                voyage_cost = int(round(distance * 0.0005 + 2.0))
                profit = sell_price - buy_price - voyage_cost
                if profit > 0:
                    candidates.append((profit, destination, sell_price, distance, voyage_cost))
            if candidates:
                profit, destination, sell_price, distance, voyage_cost = max(candidates, key=lambda item: item[0])
                routes.append({
                    "good": good, "destination": destination.name,
                    "buy": buy_price, "sell": sell_price, "profit": profit,
                    "distance": int(distance), "cost": voyage_cost,
                })
        routes.sort(key=lambda row: row["profit"], reverse=True)
        return routes[:max(1, int(limit))]

    def trade_state_for_save(self):
        return {
            "cargo_hold": dict(self.cargo_hold),
            "cargo_average_cost": dict(self.cargo_average_cost),
            "trade_ledger": dict(self.trade_ledger),
            "market_tick_timer": round(self.market_tick_timer, 2),
            "market_state": self.market_state,
            "faction_economies": self.faction_economies,
        }

    def restore_trade_state(self, saved):
        if not isinstance(saved, dict) or not saved:
            # Pre-trading saves receive fresh, balanced markets and an empty hold.
            self.cargo_hold = {}
            self.cargo_average_cost = {}
            self.trade_ledger = {"trades": 0, "gold_spent": 0, "gold_earned": 0, "realised_profit": 0, "trade_volume": 0}
            self.market_tick_timer = 0.0
            self.refresh_faction_shortages()
            return
        valid_goods = set(self.TRADE_GOODS_BY_ID)
        self.cargo_hold = {
            good_id: max(0, min(100000, int(quantity)))
            for good_id, quantity in saved.get("cargo_hold", {}).items()
            if good_id in valid_goods and int(quantity) > 0
        }
        self.cargo_average_cost = {
            good_id: max(0.0, min(1000000.0, float(value)))
            for good_id, value in saved.get("cargo_average_cost", {}).items()
            if good_id in valid_goods
        }
        ledger_defaults = {"trades": 0, "gold_spent": 0, "gold_earned": 0, "realised_profit": 0, "trade_volume": 0}
        ledger_defaults.update({key: int(value) for key, value in saved.get("trade_ledger", {}).items() if key in ledger_defaults})
        self.trade_ledger = ledger_defaults
        saved_markets = saved.get("market_state", {})
        for port in self.ports:
            source = saved_markets.get(port.name, {}) if isinstance(saved_markets, dict) else {}
            target_records = self.market_state.get(port.name, {})
            for good in self.TRADE_GOODS:
                good_id = good["id"]
                entry = source.get(good_id, {}) if isinstance(source, dict) else {}
                if not isinstance(entry, dict):
                    continue
                record = target_records[good_id]
                record["stock"] = max(0.0, min(180.0, float(entry.get("stock", record["stock"]))))
                record["demand"] = max(8, min(100, int(entry.get("demand", record["demand"]))))
                # Production/consumption belong to the port's authored market profile.
        saved_economies = saved.get("faction_economies", {})
        for faction in self.FACTION_NAMES:
            economy = self._faction_economy(faction)
            entry = saved_economies.get(faction, {}) if isinstance(saved_economies, dict) else {}
            if not isinstance(entry, dict):
                continue
            economy["treasury"] = max(0, min(10**12, int(entry.get("treasury", economy["treasury"]))))
            economy["prosperity"] = max(0.0, min(100.0, float(entry.get("prosperity", economy["prosperity"]))))
            economy["trade_balance"] = max(-(10**12), min(10**12, int(entry.get("trade_balance", 0))))
            economy["trade_volume"] = max(0, min(10**12, int(entry.get("trade_volume", 0))))
            economy["shortage_pressure"] = max(0.0, min(100.0, float(entry.get("shortage_pressure", 0.0))))
        self.market_tick_timer = max(0.0, min(self.MARKET_TICK_SECONDS, float(saved.get("market_tick_timer", 0.0))))
        # A manually edited save cannot load more cargo than the ship can carry.
        overflow = self.cargo_load() - self.cargo_capacity()
        if overflow > 0.001:
            for good in reversed(self.TRADE_GOODS):
                good_id = good["id"]
                quantity = self.cargo_quantity(good_id)
                if quantity <= 0:
                    continue
                remove = min(quantity, int(math.ceil(overflow / good["space"])))
                self.cargo_hold[good_id] = quantity - remove
                if self.cargo_hold[good_id] <= 0:
                    self.cargo_hold.pop(good_id, None)
                    self.cargo_average_cost.pop(good_id, None)
                overflow = self.cargo_load() - self.cargo_capacity()
                if overflow <= 0.001:
                    break
            if hasattr(self, "add_journal"):
                self.add_journal("The saved cargo manifest exceeded the ship's hold. Excess cargo was jettisoned during loading.")
        self.refresh_faction_shortages()

    def trade_market_layout(self):
        width, height = self.screen.get_size()
        panel_width = min(1220, width - 32)
        panel_height = min(742, height - 28)
        panel = pygame.Rect((width - panel_width) // 2, (height - panel_height) // 2, panel_width, panel_height)
        left_x = panel.x + 24
        left_width = int(panel.width * 0.51)
        rows_top = panel.y + 142
        rows_bottom = panel.bottom - 174
        row_height = max(14, min(34, (rows_bottom - rows_top) // len(self.TRADE_GOODS)))
        rows = [pygame.Rect(left_x, rows_top + index * row_height, left_width, row_height - 3)
                for index in range(len(self.TRADE_GOODS))]
        right_x = left_x + left_width + 22
        right_width = panel.right - 24 - right_x
        quantity_buttons = [pygame.Rect(right_x + index * (right_width // 3 + 5), panel.bottom - 158,
                                         max(56, right_width // 3 - 7), 34) for index in range(3)]
        buy_button = pygame.Rect(right_x, panel.bottom - 110, (right_width - 10) // 2, 42)
        sell_button = pygame.Rect(buy_button.right + 10, panel.bottom - 110, (right_width - 10) // 2, 42)
        close_button = pygame.Rect(panel.right - 128, panel.y + 20, 100, 34)
        return panel, rows, right_x, right_width, quantity_buttons, buy_button, sell_button, close_button

    def handle_trade_market_click(self, position):
        if not self.market_open:
            return False
        panel, rows, right_x, right_width, qty_buttons, buy_button, sell_button, close_button = self.trade_market_layout()
        if close_button.collidepoint(position) or not panel.collidepoint(position):
            self.close_trade_market()
            return True
        for index, rect in enumerate(rows):
            if rect.collidepoint(position):
                self.market_selection = index
                return True
        for index, rect in enumerate(qty_buttons):
            if rect.collidepoint(position):
                self.market_quantity_index = index
                return True
        good_id = self.selected_trade_good()["id"]
        if buy_button.collidepoint(position):
            self.buy_trade_cargo(good_id)
            return True
        if sell_button.collidepoint(position):
            self.sell_trade_cargo(good_id)
            return True
        return True

    def handle_trade_market_key(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_y):
            self.close_trade_market()
        elif key in (pygame.K_UP, pygame.K_w):
            self.market_selection = (self.market_selection - 1) % len(self.TRADE_GOODS)
        elif key == pygame.K_DOWN:
            self.market_selection = (self.market_selection + 1) % len(self.TRADE_GOODS)
        elif key == pygame.K_LEFT:
            self.market_quantity_index = max(0, self.market_quantity_index - 1)
        elif key == pygame.K_RIGHT:
            self.market_quantity_index = min(2, self.market_quantity_index + 1)
        elif key in (pygame.K_b, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.buy_trade_cargo(self.selected_trade_good()["id"])
        elif key == pygame.K_s:
            self.sell_trade_cargo(self.selected_trade_good()["id"])

    def draw_trade_market(self):
        if not self.market_open or not self.docked_port:
            return
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((7, 15, 17, 218))
        self.screen.blit(overlay, (0, 0))
        panel, rows, right_x, right_width, qty_buttons, buy_button, sell_button, close_button = self.trade_market_layout()
        pygame.draw.rect(self.screen, (38, 27, 20), panel.inflate(12, 12), border_radius=9)
        pygame.draw.rect(self.screen, (225, 209, 171), panel, border_radius=7)
        pygame.draw.rect(self.screen, (143, 101, 60), panel, 3, border_radius=7)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(panel)
        port = self.ports_by_name[self.docked_port]
        title = fit_text_surface(self.big_font, f"PORT MARKET  ·  {self.docked_port.upper()}", (73, 45, 28), panel.width - 170, 48)
        self.screen.blit(title, (panel.x + 24, panel.y + 14))
        economy = self.faction_economy_summary(port.faction)
        subtitle_text = (f"{port.faction}  ·  {self.faction_attitude(port.faction)}  ·  Local prosperity {economy['prosperity']:.0f}/100  ·  "
                         f"Shortage pressure {economy['shortage_pressure']:.0f}%")
        subtitle = fit_text_surface(self.small_font, subtitle_text, (103, 74, 47), panel.width - 52, 26)
        self.screen.blit(subtitle, (panel.x + 26, panel.y + 76))
        pygame.draw.line(self.screen, (151, 111, 69), (panel.x + 24, panel.y + 110), (panel.right - 24, panel.y + 110), 2)

        header_y = panel.y + 116
        columns = (rows[0].x + 8, rows[0].x + int(rows[0].width * 0.51), rows[0].x + int(rows[0].width * 0.70), rows[0].x + int(rows[0].width * 0.85))
        headers = [("COMMODITY", columns[0]), ("STOCK", columns[1]), ("BUY", columns[2]), ("SELL", columns[3])]
        for label, x in headers:
            text = fit_text_surface(self.tiny_font, label, (107, 76, 47), 90, 22)
            self.screen.blit(text, (x, header_y))
        for index, row in enumerate(rows):
            good = self.TRADE_GOODS[index]
            selected = index == self.market_selection
            color = (197, 177, 139) if selected else ((224, 209, 177) if index % 2 == 0 else (214, 198, 164))
            pygame.draw.rect(self.screen, color, row, border_radius=3)
            if selected:
                pygame.draw.rect(self.screen, (110, 67, 36), row, 2, border_radius=3)
            record = self.market_record(port.name, good["id"])
            values = (
                (good["name"], columns[0], 150),
                (f"{record['stock']:.0f}", columns[1], 54),
                (f"{self.market_buy_price(port.name, good['id'])}g", columns[2], 66),
                (f"{self.market_sell_price(port.name, good['id'])}g", columns[3], 66),
            )
            for value, x, max_width in values:
                text = fit_text_surface(self.tiny_font, value, (64, 46, 31), max_width, row.height - 4)
                self.screen.blit(text, (x, row.y + 1))

        selected_good = self.selected_trade_good()
        good_id = selected_good["id"]
        record = self.market_record(port.name, good_id)
        buy_price = self.market_buy_price(port.name, good_id)
        sell_price = self.market_sell_price(port.name, good_id)
        right_top = panel.y + 124
        heading = fit_text_surface(self.font, selected_good["name"], (70, 44, 27), right_width, 34)
        self.screen.blit(heading, (right_x, right_top))
        description = fit_text_surface(self.tiny_font, selected_good["description"], (102, 76, 49), right_width, 43)
        self.screen.blit(description, (right_x, right_top + 38))
        stat_lines = [
            f"Buy {buy_price} gold/unit  ·  Sell {sell_price} gold/unit  ·  {self.market_status(port.name, good_id)}",
            f"Warehouse stock {record['stock']:.0f}  ·  Demand {record['demand']}/100  ·  Port production {record['production']:.1f}/cycle",
            f"In your hold: {self.cargo_quantity(good_id)}  ·  Average cost {self.cargo_average_cost.get(good_id, 0.0):.1f} gold/unit",
        ]
        for line_index, line in enumerate(stat_lines):
            text = fit_text_surface(self.tiny_font, line, (84, 61, 40), right_width, 24)
            self.screen.blit(text, (right_x, right_top + 88 + line_index * 27))

        capacity = self.cargo_capacity()
        loaded = self.cargo_load()
        bar_rect = pygame.Rect(right_x, right_top + 174, right_width, 15)
        pygame.draw.rect(self.screen, (97, 80, 57), bar_rect, border_radius=3)
        fill = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * min(1.0, loaded / max(1.0, capacity))), bar_rect.height)
        pygame.draw.rect(self.screen, (79, 129, 86), fill, border_radius=3)
        pygame.draw.rect(self.screen, (116, 83, 52), bar_rect, 1, border_radius=3)
        capacity_text = fit_text_surface(self.tiny_font, f"CARGO HOLD  {loaded:.1f} / {capacity:.0f} units  ·  {self.cargo_free_space():.1f} free", (83, 59, 38), right_width, 22)
        self.screen.blit(capacity_text, (right_x, bar_rect.y + 19))
        manifest = [f"{self.TRADE_GOODS_BY_ID[gid]['name']} ×{qty}" for gid, qty in self.cargo_hold.items() if qty > 0]
        manifest_text = "Manifest: " + (", ".join(manifest[:3]) if manifest else "empty")
        if len(manifest) > 3:
            manifest_text += f" +{len(manifest) - 3} more"
        manifest_surface = fit_text_surface(self.tiny_font, manifest_text, (91, 69, 45), right_width, 21)
        self.screen.blit(manifest_surface, (right_x, bar_rect.y + 40))

        route_top = right_top + 246
        route_title = fit_text_surface(self.small_font, "PROFITABLE ROUTES FROM THIS HARBOUR", (87, 57, 34), right_width, 26)
        self.screen.blit(route_title, (right_x, route_top))
        routes = self.best_trade_routes(port.name, 4)
        if routes:
            for index, route in enumerate(routes):
                line = f"{route['good']['name']} → {route['destination']}   +{route['profit']}g/unit   ({route['distance']:,} units)"
                route_surface = fit_text_surface(self.tiny_font, line, (70, 92, 60), right_width, 22)
                self.screen.blit(route_surface, (right_x, route_top + 31 + index * 23))
        else:
            no_route = fit_text_surface(self.tiny_font, "No clear profit at current prices. Check again after markets shift.", (111, 80, 53), right_width, 23)
            self.screen.blit(no_route, (right_x, route_top + 32))

        qty_label = fit_text_surface(self.tiny_font, "TRADE QUANTITY", (99, 72, 45), right_width, 20)
        self.screen.blit(qty_label, (right_x, panel.bottom - 189))
        for index, rect in enumerate(qty_buttons):
            selected = index == self.market_quantity_index
            pygame.draw.rect(self.screen, (94, 119, 77) if selected else (142, 111, 75), rect, border_radius=4)
            pygame.draw.rect(self.screen, (225, 206, 165), rect, 2 if selected else 1, border_radius=4)
            label = str(self.TRADE_QUANTITY_OPTIONS[index])
            text = fit_text_surface(self.small_font, label, (255, 240, 211), rect.width - 8, rect.height - 6)
            self.screen.blit(text, text.get_rect(center=rect.center))
        pygame.draw.rect(self.screen, (57, 111, 71), buy_button, border_radius=4)
        pygame.draw.rect(self.screen, (230, 211, 170), buy_button, 2, border_radius=4)
        buy_text = fit_text_surface(self.small_font, f"BUY  ·  {buy_price}g each", (255, 242, 214), buy_button.width - 10, buy_button.height - 8)
        self.screen.blit(buy_text, buy_text.get_rect(center=buy_button.center))
        pygame.draw.rect(self.screen, (120, 79, 51), sell_button, border_radius=4)
        pygame.draw.rect(self.screen, (230, 211, 170), sell_button, 2, border_radius=4)
        sell_text = fit_text_surface(self.small_font, f"SELL  ·  {sell_price}g each", (255, 242, 214), sell_button.width - 10, sell_button.height - 8)
        self.screen.blit(sell_text, sell_text.get_rect(center=sell_button.center))
        pygame.draw.rect(self.screen, (116, 79, 49), close_button, border_radius=4)
        close_text = fit_text_surface(self.tiny_font, "CLOSE  (Y)", (255, 240, 213), close_button.width - 8, close_button.height - 6)
        self.screen.blit(close_text, close_text.get_rect(center=close_button.center))
        footer_text = "Up/Down: commodity  ·  Left/Right: quantity  ·  B/Enter: buy  ·  S: sell  ·  Esc: close"
        footer = fit_text_surface(self.tiny_font, footer_text, (108, 78, 49), panel.width - 50, 22)
        self.screen.blit(footer, footer.get_rect(midbottom=(panel.centerx, panel.bottom - 8)))
        self.screen.set_clip(previous_clip)


TradeMixin.TRADE_GOODS_BY_ID = {good["id"]: good for good in TradeMixin.TRADE_GOODS}
