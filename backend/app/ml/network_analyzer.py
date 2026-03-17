"""Network analyzer for detecting fraud rings via graph analysis.

Builds a transaction graph and computes centrality and community metrics
to identify suspicious clusters of entities.
"""

from collections import defaultdict
from typing import Any

import structlog

logger = structlog.get_logger()


class NetworkAnalyzer:
    """Graph-based network analysis for fraud ring detection."""

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("network_analyzer_loaded")

    def analyze(self, entity_id: str, transactions: list[dict]) -> dict[str, Any]:
        """Analyze the transaction network around an entity."""
        if not transactions:
            return _empty_result()

        graph = _build_adjacency(transactions)
        degree = len(graph.get(entity_id, set()))
        total_nodes = len(graph)
        total_edges = sum(len(v) for v in graph.values()) // 2

        component = _bfs_component(graph, entity_id)
        component_size = len(component)

        degree_centrality = degree / (total_nodes - 1) if total_nodes > 1 else 0.0
        density = (2 * total_edges) / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0.0

        risk_signals = 0
        if degree_centrality > 0.3:
            risk_signals += 1
        if component_size > 10:
            risk_signals += 1
        if density > 0.5:
            risk_signals += 1

        network_score = min(risk_signals / 3.0, 1.0)

        return {
            "network_score": round(network_score, 4),
            "degree": degree,
            "degree_centrality": round(degree_centrality, 4),
            "component_size": component_size,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "density": round(density, 4),
            "risk_signals": risk_signals,
            "model_type": "network_analyzer",
            "model_version": "dev-1.0",
        }


def _build_adjacency(transactions: list[dict]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for txn in transactions:
        src = str(txn.get("source_entity_id", ""))
        dst = str(txn.get("destination_entity_id", ""))
        if src and dst and src != dst:
            graph[src].add(dst)
            graph[dst].add(src)
    return dict(graph)


def _bfs_component(graph: dict[str, set[str]], start: str) -> set[str]:
    visited: set[str] = set()
    queue = [start]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                queue.append(neighbor)
    return visited


def _empty_result() -> dict[str, Any]:
    return {
        "network_score": 0.0,
        "degree": 0,
        "degree_centrality": 0.0,
        "component_size": 1,
        "total_nodes": 1,
        "total_edges": 0,
        "density": 0.0,
        "risk_signals": 0,
        "model_type": "network_analyzer",
        "model_version": "dev-1.0",
    }
