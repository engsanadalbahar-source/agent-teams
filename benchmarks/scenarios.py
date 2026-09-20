"""
Defines realistic software engineering scenarios for benchmarking:
1. Feature Delivery (Checkout Discount Engine with existing codebase context)
2. Bug Investigation (Payment Webhook Failure with massive server logs)
3. Multi-Module Refactoring (Decoupled micro-services migration)
"""

# Common Realistic Payloads

ORDER_SERVICE_CODE = """
import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from .models import Order, OrderItem, Customer, Discount, OrderStatus

class OrderService:
    def __init__(self, db_session, inventory_client, payment_gateway, notifier):
        self.db = db_session
        self.inventory = inventory_client
        self.payment = payment_gateway
        self.notifier = notifier

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.db.query(Order).filter(Order.id == order_id).first()

    def create_order(self, customer_id: str, items: List[Dict[str, Any]]) -> Order:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        order = Order(
            customer_id=customer_id,
            status=OrderStatus.PENDING,
            created_at=datetime.datetime.utcnow(),
            items=[]
        )
        subtotal = Decimal("0.00")
        for item_data in items:
            sku = item_data["sku"]
            qty = item_data["quantity"]
            price = Decimal(str(item_data["unit_price"]))
            if not self.inventory.check_stock(sku, qty):
                raise ValueError(f"Insufficient inventory for {sku}")
            item = OrderItem(sku=sku, quantity=qty, unit_price=price, subtotal=price * qty)
            order.items.append(item)
            subtotal += item.subtotal

        order.subtotal = subtotal
        order.tax = subtotal * Decimal("0.08")  # Basic fixed tax
        order.total = order.subtotal + order.tax
        self.db.add(order)
        self.db.commit()
        return order

    def cancel_order(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        if order.status in [OrderStatus.SHIPPED, OrderStatus.COMPLETED]:
            raise ValueError("Cannot cancel fulfilled order")
        order.status = OrderStatus.CANCELLED
        self.db.commit()
        return order
"""

MODELS_CODE = """
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import datetime

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

@dataclass
class OrderItem:
    sku: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

@dataclass
class Customer:
    id: str
    name: str
    email: str
    tier: str  # 'STANDARD', 'SILVER', 'GOLD', 'VIP'

@dataclass
class Discount:
    code: str
    percentage: Decimal
    min_subtotal: Decimal
    active: bool

@dataclass
class Order:
    id: str
    customer_id: str
    status: OrderStatus
    created_at: datetime.datetime
    items: List[OrderItem]
    subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
"""

PRICING_RULES_JSON = """{
  "tax_rates": {
    "US-CA": 0.0925,
    "US-NY": 0.08875,
    "US-TX": 0.0825,
    "DEFAULT": 0.05
  },
  "tier_discounts": {
    "STANDARD": 0.0,
    "SILVER": 0.05,
    "GOLD": 0.10,
    "VIP": 0.20
  },
  "max_stackable_discount": 0.35,
  "free_shipping_threshold": 50.00
}"""

# A simulated 14,000-token server log file with thread dumps and stack traces
SERVER_LOGS_SAMPLE = """
2026-09-20 10:14:02.102 [webhook-worker-4] ERROR c.p.service.WebhookHandler - Failed to process webhook event evt_998124
java.util.concurrent.CompletionException: org.postgresql.util.PSQLException: ERROR: deadlock detected
  Detail: Process 4129 waits for ShareLock on transaction 8812739; blocked by process 4132.
  Process 4132 waits for ExclusiveLock on tuple (42, 19) of relation "payment_intents"; blocked by process 4129.
  Hint: See server log for query details.
\tat java.base/java.util.concurrent.CompletableFuture.encodeThrowable(CompletableFuture.java:315)
\tat java.base/java.util.concurrent.CompletableFuture.completeThrowable(CompletableFuture.java:320)
\tat com.payment.service.WebhookHandler.lambda$handleChargeSucceeded$2(WebhookHandler.java:184)
\tat java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)
\tat java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)
\tat java.base/java.lang.Thread.run(Thread.java:840)
Caused by: org.postgresql.util.PSQLException: ERROR: deadlock detected
\tat org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(QueryExecutorImpl.java:2675)
\tat org.postgresql.core.v3.QueryExecutorImpl.processResults(QueryExecutorImpl.java:2365)
\tat org.postgresql.core.v3.QueryExecutorImpl.execute(QueryExecutorImpl.java:355)
\tat org.postgresql.jdbc.PgStatement.executeInternal(PgStatement.java:490)
\tat org.postgresql.jdbc.PgPreparedStatement.executeUpdate(PgPreparedStatement.java:134)
\tat com.payment.dao.PaymentIntentDao.updateStatusWithLock(PaymentIntentDao.java:77)
\tat com.payment.service.WebhookHandler.handleChargeSucceeded(WebhookHandler.java:162)
""" * 18  # Repeat to simulate real-world log bundle (~12,000 tokens)


def run_scenario_feature_delivery(tracker_mono, tracker_agent_teams):
    """
    Scenario 1: Feature Delivery (E-Commerce Multi-tier Discounts)
    Compares Monolithic vs AgentTeams execution.
    """
    # -------------------------------------------------------------
    # 1. Monolithic Execution
    # -------------------------------------------------------------
    user_prompt = "Implement tiered customer discounts and state-based tax calculation in OrderService."
    
    # Turn 1: Mono reads all 3 codebase files
    tool_input_1 = f"{user_prompt}\n\n[Tool: view_file order_service.py]\n{ORDER_SERVICE_CODE}\n[Tool: view_file models.py]\n{MODELS_CODE}\n[Tool: view_file pricing_rules.json]\n{PRICING_RULES_JSON}"
    assistant_1 = "I have reviewed order_service.py, models.py, and pricing_rules.json. I will write unit tests for the discount and tax calculation, then implement the new logic."
    tracker_mono.add_turn(tool_input_1, assistant_1)

    # Turn 2: Mono writes tests
    tool_input_2 = "Proceed with writing the tests."
    assistant_2 = """[Tool: write_to_file tests/test_order_service.py]
def test_tiered_discounts_vip():
    # Test 20% discount on VIP customer
    ...
def test_state_tax_calculation():
    # Test US-CA 9.25% tax
    ...
"""
    tracker_mono.add_turn(tool_input_2, assistant_2)

    # Turn 3: Mono updates order_service.py
    tool_input_3 = "Now implement the logic in OrderService."
    assistant_3 = """[Tool: replace_file_content order_service.py]
# Replaced create_order with tiered discount calculation and state-based tax lookup
"""
    tracker_mono.add_turn(tool_input_3, assistant_3)

    # Turn 4: Mono runs pytest -> fails with stack trace
    tool_input_4 = """[Tool: run_command pytest]
FAILED tests/test_order_service.py::test_tiered_discounts_vip - AssertionError: 80.00 != 85.00
Stack trace:
  File "tests/test_order_service.py", line 24, in test_tiered_discounts_vip
    assert order.total == Decimal("80.00")
E   AssertionError: assert Decimal('85.00') == Decimal('80.00')
E     +Decimal('85.00')
E     -Decimal('80.00')
"""
    assistant_4 = "The discount was applied before tax calculation, but tax was computed on subtotal instead of discounted subtotal. Fixing now."
    tracker_mono.add_turn(tool_input_4, assistant_4)

    # Turn 5: Mono fixes bug
    tool_input_5 = "Proceed with the fix."
    assistant_5 = """[Tool: replace_file_content order_service.py]
# Fixed: taxable_amount = subtotal - discount_amount
"""
    tracker_mono.add_turn(tool_input_5, assistant_5)

    # Turn 6: Mono runs pytest -> passes
    tool_input_6 = "[Tool: run_command pytest]\npytest passed: 4 passed in 0.12s"
    assistant_6 = "All tests now pass. Now reviewing the code changes for edge cases and security."
    tracker_mono.add_turn(tool_input_6, assistant_6)

    # Turn 7: Mono reviews diff & generates changelog
    tool_input_7 = "Run code review."
    assistant_7 = "Review passed: No unhandled nulls, precision uses Decimal, git diff is clean."
    tracker_mono.add_turn(tool_input_7, assistant_7)

    # Turn 8: Mono delivers final response
    tool_input_8 = "Finalize and summarize."
    assistant_8 = "Feature complete: Multi-tier discounts and state-based taxes implemented and verified."
    tracker_mono.add_turn(tool_input_8, assistant_8)

    # -------------------------------------------------------------
    # 2. AgentTeams Execution (Captain + Isolated Subagents)
    # -------------------------------------------------------------
    captain = tracker_agent_teams["captain"]
    analyst = tracker_agent_teams["analyst"]
    architect = tracker_agent_teams["architect"]
    implementer = tracker_agent_teams["implementer"]
    qa = tracker_agent_teams["qa"]
    reviewer = tracker_agent_teams["reviewer"]

    # Step A: Captain initializes DAG
    captain.add_turn(
        user_prompt,
        "Creating task DAG: 1. analyst (reqs) -> 2. architect (spec) -> 3. qa (tests) -> 4. implementer (code) -> 5. qa (verify) -> 6. reviewer (audit)."
    )

    # Step B: Analyst reads files and generates compact Requirements Contract
    analyst.add_turn(
        f"Analyze requirements for tiered discounts and state tax.\n[Tool: view_file order_service.py]\n{ORDER_SERVICE_CODE}\n[Tool: view_file models.py]\n{MODELS_CODE}\n[Tool: view_file pricing_rules.json]\n{PRICING_RULES_JSON}",
        """CONTRACT:
- VIP gets 20%, GOLD 10%, SILVER 5%, STANDARD 0%.
- Tax is calculated on (subtotal - discount_amount).
- State tax uses state_rates map in pricing_rules.json, defaulting to 5%."""
    )
    # Analyst context terminates here.

    # Step C: Architect produces interface spec
    architect.add_turn(
        "CONTRACT:\n- VIP gets 20%, GOLD 10%, SILVER 5%.\n- Tax on (subtotal - discount).\nSpecify interface changes.",
        "SPEC: In OrderService.create_order: add `state: str = 'DEFAULT'` parameter. Update order.discount_amount and order.tax."
    )

    # Step D: QA writes unit tests based on spec
    qa.add_turn(
        "SPEC: In OrderService.create_order: add `state: str`. Test VIP 20% discount and CA tax on discounted amount.",
        """[Tool: write_to_file tests/test_order_service.py]
def test_tiered_discounts_vip(): ...
def test_state_tax_calculation(): ..."""
    )

    # Step E: Implementer implements logic (receives ONLY spec + relevant function snippet)
    implementer.add_turn(
        f"SPEC: Add state-based tax & tiered discount to create_order.\nSnippet:\n{ORDER_SERVICE_CODE[:600]}",
        "[Tool: replace_file_content order_service.py]\n# Implemented discount and tax logic"
    )

    # Step F: QA runs tests, finds bug, reports targeted finding to Implementer
    qa.add_turn(
        """[Tool: run_command pytest]
FAILED tests/test_order_service.py::test_tiered_discounts_vip - AssertionError: 85.00 != 80.00""",
        "FINDING: Tax was calculated on subtotal instead of (subtotal - discount). Remediation: tax = (subtotal - discount) * tax_rate."
    )

    # Step G: Implementer fixes targeted finding
    implementer.add_turn(
        "FINDING: Tax was calculated on subtotal instead of (subtotal - discount).",
        "[Tool: replace_file_content order_service.py]\n# Fixed taxable amount calculation."
    )

    # Step H: QA verifies fix
    qa.add_turn(
        "[Tool: run_command pytest]\npytest passed: 4 passed in 0.12s",
        "VERIFICATION: All 4 tests passed."
    )

    # Step I: Reviewer reviews git diff
    reviewer.add_turn(
        "REVIEW CONTRACT: Verify diff matches inScope ['order_service.py'] and zero high/blocker findings.\n[Tool: git diff order_service.py]\n+ discount_amount calculation\n+ tax on discounted amount",
        '{"verdict": "pass", "findings": [], "scopeAudit": {"status": "clean"}}'
    )

    # Step J: Captain finalizes
    captain.add_turn(
        "Task completed: review passed with verdict 'pass'.",
        "Feature delivery complete: Tiered discounts and state taxes implemented, verified, and audited."
    )


def run_scenario_bug_investigation(tracker_mono, tracker_agent_teams):
    """
    Scenario 2: Bug Investigation with Massive Server Logs (~12,000 tokens)
    Compares Monolithic vs AgentTeams execution.
    """
    # -------------------------------------------------------------
    # 1. Monolithic Execution
    # -------------------------------------------------------------
    user_prompt = "Investigate the webhook deadlock error in our production logs and patch it."

    # Turn 1: Ingest massive log
    tool_input_1 = f"{user_prompt}\n\n[Server Logs Dump]\n{SERVER_LOGS_SAMPLE}"
    assistant_1 = "I see a PostgreSQL deadlock between process 4129 and 4132 on the payment_intents table. Let me check the code in WebhookHandler.java."
    tracker_mono.add_turn(tool_input_1, assistant_1)

    # Turn 2: View code
    tool_input_2 = "[Tool: view_file WebhookHandler.java]\nvoid handleChargeSucceeded(...) { ... }"
    assistant_2 = "The deadlock occurs because handleChargeSucceeded acquires locks in arbitrary order. I will write a reproduction test."
    tracker_mono.add_turn(tool_input_2, assistant_2)

    # Turn 3: Write reproduction test
    tool_input_3 = "Write reproduction test."
    assistant_3 = "[Tool: write_to_file WebhookDeadlockTest.java]\n// Simulates concurrent webhook events"
    tracker_mono.add_turn(tool_input_3, assistant_3)

    # Turn 4: Apply patch
    tool_input_4 = "Apply surgical fix."
    assistant_4 = "[Tool: replace_file_content WebhookHandler.java]\n// Sort resource IDs before acquiring locks to prevent deadlock"
    tracker_mono.add_turn(tool_input_4, assistant_4)

    # Turn 5: Verify
    tool_input_5 = "[Tool: run_command ./gradlew test]\nBUILD SUCCESSFUL in 4s"
    assistant_5 = "Deadlock reproduction test passed cleanly after the patch."
    tracker_mono.add_turn(tool_input_5, assistant_5)

    # Turn 6: Summary
    tool_input_6 = "Summarize resolution."
    assistant_6 = "Deadlock resolved by enforcing canonical ordering on lock acquisitions."
    tracker_mono.add_turn(tool_input_6, assistant_6)

    # -------------------------------------------------------------
    # 2. AgentTeams Execution
    # -------------------------------------------------------------
    captain = tracker_agent_teams["captain"]
    detective = tracker_agent_teams["detective"]
    implementer = tracker_agent_teams["implementer"]
    reviewer = tracker_agent_teams["reviewer"]

    # Captain dispatches detective
    captain.add_turn(
        user_prompt,
        "Dispatching Detective subagent to isolate root cause from production logs."
    )

    # Detective ingests massive log (Context isolated to Detective only!)
    detective.add_turn(
        f"Analyze root cause from logs:\n{SERVER_LOGS_SAMPLE}",
        "ROOT CAUSE: PostgreSQL deadlock on payment_intents table due to un-ordered lock acquisition in WebhookHandler.java:162. Remediation: Sort IDs before locking."
    )
    # Detective context terminates!

    # Implementer receives ONLY the 3-line root cause diagnosis
    implementer.add_turn(
        "ROOT CAUSE: PostgreSQL deadlock on payment_intents table in WebhookHandler.java:162. Remediation: Sort IDs before locking.",
        "[Tool: replace_file_content WebhookHandler.java]\n// Enforced canonical sort ordering on lock acquisition"
    )

    # Reviewer inspects diff
    reviewer.add_turn(
        "Verify lock ordering fix in WebhookHandler.java diff.\n[git diff WebhookHandler.java]",
        '{"verdict": "pass", "findings": [], "scopeAudit": {"status": "clean"}}'
    )

    # Captain delivers report
    captain.add_turn(
        "Fix verified and review passed.",
        "Deadlock resolved by ordering lock acquisition in WebhookHandler.java."
    )


def run_scenario_multi_module_refactor(tracker_mono, tracker_agent_teams):
    """
    Scenario 3: Multi-Module Refactoring (Auth, Payments, Notifications)
    Compares Monolithic vs AgentTeams execution.
    """
    # -------------------------------------------------------------
    # 1. Monolithic Execution
    # -------------------------------------------------------------
    user_prompt = "Refactor Auth, Payment, and Notification modules to use new AsyncResult envelope."

    # Turn 1: Refactor Auth
    t1_in = f"{user_prompt}\n[Tool: view_file auth_service.py]\nclass AuthService: ... (200 lines)"
    t1_out = "[Tool: replace_file_content auth_service.py]\n# Refactored AuthService to return AsyncResult"
    tracker_mono.add_turn(t1_in, t1_out)

    # Turn 2: Test Auth
    t2_in = "[Tool: run_command pytest tests/test_auth.py]\n12 passed"
    t2_out = "AuthService tests passed. Now moving to PaymentGateway."
    tracker_mono.add_turn(t2_in, t2_out)

    # Turn 3: Refactor Payment
    t3_in = "[Tool: view_file payment_gateway.py]\nclass PaymentGateway: ... (250 lines)"
    t3_out = "[Tool: replace_file_content payment_gateway.py]\n# Refactored PaymentGateway to return AsyncResult"
    tracker_mono.add_turn(t3_in, t3_out)

    # Turn 4: Test Payment
    t4_in = "[Tool: run_command pytest tests/test_payment.py]\n15 passed"
    t4_out = "PaymentGateway tests passed. Now moving to NotificationWorker."
    tracker_mono.add_turn(t4_in, t4_out)

    # Turn 5: Refactor Notifications
    t5_in = "[Tool: view_file notification_worker.py]\nclass NotificationWorker: ... (220 lines)"
    t5_out = "[Tool: replace_file_content notification_worker.py]\n# Refactored NotificationWorker to return AsyncResult"
    tracker_mono.add_turn(t5_in, t5_out)

    # Turn 6: Test Notifications
    t6_in = "[Tool: run_command pytest tests/test_notifications.py]\n8 passed"
    t6_out = "NotificationWorker tests passed. All 3 modules refactored."
    tracker_mono.add_turn(t6_in, t6_out)

    # Turn 7: Integration review
    t7_in = "Verify all integration tests."
    t7_out = "[Tool: run_command pytest tests/]\n35 passed in 1.4s. Refactor complete."
    tracker_mono.add_turn(t7_in, t7_out)

    # -------------------------------------------------------------
    # 2. AgentTeams Execution
    # -------------------------------------------------------------
    captain = tracker_agent_teams["captain"]
    auth_worker = tracker_agent_teams["auth_worker"]
    pay_worker = tracker_agent_teams["pay_worker"]
    notif_worker = tracker_agent_teams["notif_worker"]

    captain.add_turn(
        user_prompt,
        "Dispatching 3 parallel worker subagents with bounded inScope contracts: auth, payment, notification."
    )

    auth_worker.add_turn(
        "inScope: ['services/auth/**']\nRefactor AuthService to use AsyncResult.\n[Tool: view_file auth_service.py]",
        "[Tool: replace_file_content auth_service.py]\n[Tool: run_command pytest tests/test_auth.py]\n12 passed. Task complete."
    )

    pay_worker.add_turn(
        "inScope: ['services/payment/**']\nRefactor PaymentGateway to use AsyncResult.\n[Tool: view_file payment_gateway.py]",
        "[Tool: replace_file_content payment_gateway.py]\n[Tool: run_command pytest tests/test_payment.py]\n15 passed. Task complete."
    )

    notif_worker.add_turn(
        "inScope: ['services/notification/**']\nRefactor NotificationWorker to use AsyncResult.\n[Tool: view_file notification_worker.py]",
        "[Tool: replace_file_content notification_worker.py]\n[Tool: run_command pytest tests/test_notifications.py]\n8 passed. Task complete."
    )

    captain.add_turn(
        "All 3 modular workers reported successful verification.",
        "Integration build verified: All 3 modules cleanly migrated to AsyncResult envelope."
    )
