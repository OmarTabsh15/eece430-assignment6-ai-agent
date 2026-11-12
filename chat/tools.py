# EECE430 Assignment 3 - Omar Tabsh (202400798)
from decimal import Decimal, ROUND_HALF_UP

from .models import Item

CENTS = Decimal("0.01")


def to_money(value):
    """Round a Decimal to 2 places and return it as a float (JSON-friendly)."""
    return float(Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP))


def check_stock(name):
    """Look up how many of an item we have and its unit price."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    return {"name": item.name, "quantity": item.quantity, "price": to_money(item.price)}


def list_items():
    """Return every item in the inventory."""
    items = Item.objects.all()
    return {"items": [
        {"name": i.name, "quantity": i.quantity, "price": to_money(i.price)}
        for i in items
    ]}


def add_item(name, quantity, price=None):
    """Create a new item, or add to an existing one's stock."""
    if price is not None and price < 0:
        return {"error": "Price cannot be negative."}
    item = Item.objects.filter(name__iexact=name).first()
    if item is not None:
        item.quantity += int(quantity)
        if price is not None:
            item.price = Decimal(str(price))
        item.save()
        return {"name": item.name, "quantity": item.quantity,
                "price": to_money(item.price), "created": False}
    item = Item.objects.create(
        name=name,
        quantity=int(quantity),
        price=Decimal(str(price)) if price is not None else Decimal("0"),
    )
    return {"name": item.name, "quantity": item.quantity,
            "price": to_money(item.price), "created": True}


def remove_stock(name, quantity):
    """Take a quantity out of stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    if quantity > item.quantity:
        return {
            "error": f"Cannot remove {quantity}. Only {item.quantity} in stock.",
            "name": item.name,
            "quantity": item.quantity,
        }
    item.quantity -= quantity
    item.save()
    return {"name": item.name, "quantity": item.quantity}


def delete_item(name):
    """Remove an item from the inventory entirely."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.delete()
    return {"deleted": name}


def set_price(name, price):
    """Change the unit price of an existing item."""
    if price < 0:
        return {"error": "Price cannot be negative."}
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.price = Decimal(str(price))
    item.save()
    return {"name": item.name, "price": to_money(item.price)}


def calculate_cost(name, quantity, vat_percent=0):
    """Work out the cost of buying a quantity of an item, with optional VAT."""
    if quantity <= 0:
        return {"error": "Quantity must be positive."}
    if vat_percent < 0:
        return {"error": "VAT percentage cannot be negative."}
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    subtotal = item.price * int(quantity)
    vat_amount = subtotal * Decimal(str(vat_percent)) / Decimal("100")
    total = subtotal + vat_amount
    return {
        "name": item.name,
        "unit_price": to_money(item.price),
        "quantity": int(quantity),
        "subtotal": to_money(subtotal),
        "vat_percent": vat_percent,
        "vat_amount": to_money(vat_amount),
        "total": to_money(total),
    }


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "check_stock",
        "description": "Look up the current quantity and unit price of a single item in the inventory. Use this whenever the user asks whether something is in stock, how many there are, or how much one costs.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_items",
        "description": "Return every item in the inventory with its quantity and unit price. Use this when the user asks what is in stock generally, or asks for a list, rather than about one specific item.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "add_item",
        "description": "Add stock to the inventory. If the item does not exist it is created; if it already exists the quantity is added to the existing total. Use this for restocking and for new deliveries. If a price is given it becomes the item's unit price.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to add. Must be positive.",
                },
                "price": {
                    "type": "number",
                    "description": "Optional unit price of the item in dollars, e.g. 2.5.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "remove_stock",
        "description": "Reduce the quantity of an existing item. Use this when items are sold, shipped or used. This does NOT delete the item; it only lowers the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to remove. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "delete_item",
        "description": "Permanently remove an item and its record from the inventory entirely. This is destructive. Only use it when the user clearly wants the item gone, not when they want to reduce its quantity.",
        "parameters": {
            "type": "object",
            "properties": {

                "name": {
                    "type": "string",
                    "description": "The name of the item to delete.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "set_price",
        "description": "Set or change the unit price of an existing item. Use this when the user wants to update what an item costs.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "price": {
                    "type": "number",
                    "description": "The new unit price in dollars, e.g. 2.5.",
                },
            },
            "required": ["name", "price"],
        },
    },
    {
        "type": "function",
        "name": "calculate_cost",
        "description": "Calculate the cost of buying a number of units of an item, using the item's unit price from the inventory, and optionally add a VAT (tax) percentage. Returns the subtotal, the VAT amount and the total. Use this whenever the user asks how much some quantity of an item costs.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Chocolate Bar'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units are being bought. Must be positive.",
                },
                "vat_percent": {
                    "type": "number",
                    "description": "VAT percentage to add on top of the subtotal, e.g. 10 for 10%. Use 0 if no VAT is mentioned.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_stock": check_stock,
    "list_items": list_items,
    "add_item": add_item,
    "remove_stock": remove_stock,
    "delete_item": delete_item,
    "set_price": set_price,
    "calculate_cost": calculate_cost,
}
