"""
Unit tests for AgentTeams DAG engine, task contracts, and state transitions.
"""

import pytest
import fnmatch


class TaskContract:
    def __init__(self, task_id: str, kind: str, assignee: str, dependencies: list[str], in_scope: list[str] = None):
        self.id = task_id
        self.kind = kind
        self.assignee = assignee
        self.dependencies = dependencies
        self.in_scope = in_scope or []
        self.state = "pending"
        self.attempt = 1

    def can_claim(self, completed_task_ids: set[str]) -> bool:
        return all(dep in completed_task_ids for dep in self.dependencies)

    def is_file_in_scope(self, file_path: str) -> bool:
        if not self.in_scope:
            return True
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in self.in_scope)


class DAG:
    def __init__(self):
        self.tasks: dict[str, TaskContract] = {}

    def add_task(self, task: TaskContract):
        self.tasks[task.id] = task

    def detect_cycle(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for dep in self.tasks.get(node, TaskContract("", "", "", [])).dependencies:
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True
        return False


def test_dag_acyclic_standard():
    dag = DAG()
    dag.add_task(TaskContract("reqs", "requirements", "analyst", []))
    dag.add_task(TaskContract("arch", "architecture", "architect", ["reqs"]))
    dag.add_task(TaskContract("tests", "verification", "qa", ["arch"]))
    dag.add_task(TaskContract("impl", "implementation", "implementer", ["tests"]))
    dag.add_task(TaskContract("review", "review", "reviewer", ["impl"]))

    assert not dag.detect_cycle(), "Standard DAG should not have cycles"


def test_dag_cycle_detection():
    dag = DAG()
    dag.add_task(TaskContract("taskA", "implementation", "worker", ["taskB"]))
    dag.add_task(TaskContract("taskB", "review", "reviewer", ["taskA"]))

    assert dag.detect_cycle(), "Circular dependency should be detected"


def test_task_state_transition():
    task = TaskContract("impl", "implementation", "implementer", ["reqs", "arch"])
    
    # Cannot claim when dependencies are pending
    assert not task.can_claim({"reqs"})
    # Can claim once all dependencies are completed
    assert task.can_claim({"reqs", "arch"})


def test_in_scope_boundary_enforcement():
    task = TaskContract(
        "impl-order",
        "implementation",
        "implementer",
        [],
        in_scope=["src/services/order_service.py", "src/models/**"]
    )

    # Allowed paths
    assert task.is_file_in_scope("src/services/order_service.py")
    assert task.is_file_in_scope("src/models/order.py")
    assert task.is_file_in_scope("src/models/user.py")

    # Unauthorized paths
    assert not task.is_file_in_scope("package.json")
    assert not task.is_file_in_scope("src/services/payment_gateway.py")
    assert not task.is_file_in_scope(".env")


def test_repair_loop_avoids_circular_dependency():
    """
    Quality gate repair loop invariant:
    The repair task must depend on the original implementation task, NOT on the failed review task.
    """
    dag = DAG()
    dag.add_task(TaskContract("impl-1", "implementation", "implementer", []))
    dag.add_task(TaskContract("review-1", "review", "reviewer", ["impl-1"]))
    
    # Repair-1 depends on impl-1 (NOT review-1), consuming review findings
    dag.add_task(TaskContract("repair-1", "repair", "implementer", ["impl-1"]))
    dag.add_task(TaskContract("review-2", "review", "reviewer", ["repair-1"]))

    assert not dag.detect_cycle(), "Repair loop must be strictly acyclic"
