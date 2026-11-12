from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Item
from .tools import (
    TOOL_DECLARATIONS,
    TOOL_FUNCTIONS,
    add_item,
    calculate_cost,
    check_stock,
    remove_stock,
)


class InventoryToolTests(TestCase):
    def setUp(self):
        Item.objects.create(name="Hammer", quantity=10, price=Decimal("2.50"))

    def test_check_stock(self):
        self.assertEqual(
            check_stock("hammer"),
            {"name": "Hammer", "quantity": 10, "price": 2.5},
        )
        self.assertIn("error", check_stock("Saw"))

    def test_add_and_remove_stock(self):
        self.assertEqual(add_item("Hammer", 5)["quantity"], 15)
        self.assertEqual(remove_stock("Hammer", 3)["quantity"], 12)
        self.assertIn("error", remove_stock("Hammer", 100))

    def test_calculate_cost_with_vat(self):
        result = calculate_cost("Hammer", 4, vat_percent=10)
        self.assertEqual(result["subtotal"], 10.0)
        self.assertEqual(result["vat_amount"], 1.0)
        self.assertEqual(result["total"], 11.0)

    def test_every_declared_tool_has_a_function(self):
        names = {tool["name"] for tool in TOOL_DECLARATIONS}
        self.assertEqual(names, set(TOOL_FUNCTIONS))


class ChatPageTests(TestCase):
    def test_chat_page_loads(self):
        response = self.client.get(reverse("chat"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inventory Agent")
