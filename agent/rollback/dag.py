"""Action Dependency DAG and Topological Reverse Rollback Solver."""

from collections import defaultdict, deque
from typing import Dict, List, Set

from agent.runtime.contracts import Action


class DAGError(Exception):
    """Base exception for Action Dependency DAG operations."""
    pass


class DAGCycleError(DAGError):
    """Raised when an edge addition introduces a cycle in the dependency graph."""
    pass


class ActionNode:
    """Wrapper node in the Action Dependency DAG."""

    def __init__(self, action: Action) -> None:
        self.action_id: str = action.action_id
        self.step_index: int = action.step_index
        self.action: Action = action
        self.parents: Set[str] = set(action.dependencies)  # Predecessors
        self.children: Set[str] = set()                    # Successors (Descendants)


class RollbackDAGManager:
    """Maintains directional dependencies between actions and computes reverse topological rollback plans."""

    def __init__(self) -> None:
        self._nodes: Dict[str, ActionNode] = {}
        self._step_map: Dict[int, str] = {}  # step_index -> action_id

    def add_action(self, action: Action) -> ActionNode:
        """Add a runtime-approved action node to the DAG.
        
        Raises:
            DAGCycleError: If action dependencies create a cycle.
        """
        node = ActionNode(action)
        self._nodes[action.action_id] = node
        self._step_map[action.step_index] = action.action_id

        # 1. Wire parent -> child edges (where action depends on existing parents)
        for parent_id in action.dependencies:
            if parent_id in self._nodes:
                self._nodes[parent_id].children.add(action.action_id)

        # 2. Wire forward edges (where existing nodes depend on this new action)
        for existing_node in self._nodes.values():
            if action.action_id in existing_node.action.dependencies:
                node.children.add(existing_node.action_id)

        # Validate DAG acyclicity
        if self._has_cycle():
            # Rollback node addition
            for parent_id in action.dependencies:
                if parent_id in self._nodes:
                    self._nodes[parent_id].children.remove(action.action_id)
            for existing_node in self._nodes.values():
                if action.action_id in existing_node.action.dependencies:
                    node.children.remove(existing_node.action_id)
            del self._nodes[action.action_id]
            del self._step_map[action.step_index]
            raise DAGCycleError(f"Adding action '{action.action_id}' creates a cycle in the Action DAG.")

        return node

    def get_action_by_step(self, step_index: int) -> Action:
        """Retrieve action by step index."""
        if step_index not in self._step_map:
            raise DAGError(f"No action registered at step index {step_index}")
        return self._nodes[self._step_map[step_index]].action

    def get_descendants(self, action_id: str) -> Set[str]:
        """Compute the transitive closure of all downstream child actions dependent on target action_id."""
        if action_id not in self._nodes:
            return set()

        descendants: Set[str] = set()
        queue: deque = deque([action_id])

        while queue:
            curr_id = queue.popleft()
            if curr_id in self._nodes:
                for child_id in self._nodes[curr_id].children:
                    if child_id not in descendants:
                        descendants.add(child_id)
                        queue.append(child_id)

        return descendants

    def compute_reverse_topological_order(self, target_action_id: str) -> List[Action]:
        """Compute exact reverse topological rollback order for target_action_id and its descendants.
        
        Guarantees that child actions are executed in reverse dependency order before their parent action.
        """
        if target_action_id not in self._nodes:
            raise DAGError(f"Target action '{target_action_id}' not found in DAG.")

        # Set of actions to reverse: target_action_id + all descendants
        to_reverse_ids = self.get_descendants(target_action_id)
        to_reverse_ids.add(target_action_id)

        # Indegrees within the subgraph of to_reverse_ids
        in_degree: Dict[str, int] = {node_id: 0 for node_id in to_reverse_ids}
        for node_id in to_reverse_ids:
            node = self._nodes[node_id]
            for child_id in node.children:
                if child_id in to_reverse_ids:
                    in_degree[child_id] += 1

        # Standard Kahn's algorithm for forward topological sort
        queue = deque([node_id for node_id in to_reverse_ids if in_degree[node_id] == 0])
        forward_order: List[str] = []

        while queue:
            curr_id = queue.popleft()
            forward_order.append(curr_id)

            for child_id in self._nodes[curr_id].children:
                if child_id in to_reverse_ids:
                    in_degree[child_id] -= 1
                    if in_degree[child_id] == 0:
                        queue.append(child_id)

        if len(forward_order) != len(to_reverse_ids):
            raise DAGCycleError("Cycle detected during topological sorting for rollback.")

        # Reverse topological order: execute descendants first down to target_action_id
        reverse_order_ids = list(reversed(forward_order))

        return [self._nodes[node_id].action for node_id in reverse_order_ids]

    def _has_cycle(self) -> bool:
        """Kahn's algorithm cycle check for entire DAG."""
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self._nodes}
        for node in self._nodes.values():
            for child_id in node.children:
                in_degree[child_id] += 1

        queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            curr_id = queue.popleft()
            visited_count += 1

            for child_id in self._nodes[curr_id].children:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        return visited_count != len(self._nodes)
