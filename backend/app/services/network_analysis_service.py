from __future__ import annotations

import uuid
from collections import defaultdict

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction
from app.schemas.network import (
    ClusterInfo,
    ConnectionDetail,
    EntityConnectionResponse,
    NetworkAnalysisRequest,
    NetworkAnalysisResponse,
    NetworkEdge,
    NetworkGraphResponse,
    NetworkGraphStats,
    NetworkNode,
    RiskPath,
)

logger = structlog.get_logger()

_SUSPICIOUS_FRAUD_SCORE_THRESHOLD = 0.6


async def get_network_graph(
    db: AsyncSession,
    min_transactions: int = 2,
    limit: int = 200,
) -> NetworkGraphResponse:
    """Build a network graph from transaction pairs between entities.

    Nodes represent entities, edges represent aggregated transaction flows
    between entity pairs that meet the minimum transaction threshold.
    """
    edge_stmt = (
        select(
            Transaction.source_entity_id,
            Transaction.destination_entity_id,
            func.count().label("tx_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.coalesce(func.avg(Transaction.fraud_score), 0).label("avg_fraud"),
        )
        .where(
            and_(
                Transaction.source_entity_id.isnot(None),
                Transaction.destination_entity_id.isnot(None),
            )
        )
        .group_by(Transaction.source_entity_id, Transaction.destination_entity_id)
        .having(func.count() >= min_transactions)
        .order_by(func.count().desc())
        .limit(limit)
    )

    edge_rows = (await db.execute(edge_stmt)).all()

    entity_ids: set[uuid.UUID] = set()
    edges: list[NetworkEdge] = []
    adjacency: dict[str, set[str]] = defaultdict(set)

    for row in edge_rows:
        src = str(row.source_entity_id)
        dst = str(row.destination_entity_id)
        entity_ids.add(row.source_entity_id)
        entity_ids.add(row.destination_entity_id)
        adjacency[src].add(dst)
        adjacency[dst].add(src)

        edges.append(
            NetworkEdge(
                source=src,
                target=dst,
                weight=row.tx_count,
                total_amount=float(row.total_amount),
                avg_fraud_score=round(float(row.avg_fraud), 4),
                is_suspicious=float(row.avg_fraud) >= _SUSPICIOUS_FRAUD_SCORE_THRESHOLD,
            )
        )

    if not entity_ids:
        return NetworkGraphResponse(
            nodes=[], edges=[], stats=NetworkGraphStats()
        )

    entity_stmt = select(Entity).where(Entity.id.in_(entity_ids))
    entities = (await db.execute(entity_stmt)).scalars().all()

    alert_count_stmt = (
        select(FraudAlert.entity_id, func.count().label("cnt"))
        .where(FraudAlert.entity_id.in_(entity_ids))
        .group_by(FraudAlert.entity_id)
    )
    alert_rows = (await db.execute(alert_count_stmt)).all()
    alert_map: dict[str, int] = {str(r.entity_id): r.cnt for r in alert_rows}

    tx_count_stmt = (
        select(
            Transaction.source_entity_id.label("eid"),
            func.count().label("cnt"),
        )
        .where(Transaction.source_entity_id.in_(entity_ids))
        .group_by(Transaction.source_entity_id)
    )
    tx_rows = (await db.execute(tx_count_stmt)).all()
    tx_map: dict[str, int] = {str(r.eid): r.cnt for r in tx_rows}

    nodes: list[NetworkNode] = []
    for e in entities:
        eid = str(e.id)
        nodes.append(
            NetworkNode(
                id=eid,
                label=e.name,
                entity_type=e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type),
                risk_score=float(e.risk_score) if e.risk_score else 0.0,
                risk_level=e.risk_level.value if hasattr(e.risk_level, "value") else str(e.risk_level),
                alert_count=alert_map.get(eid, 0),
                transaction_count=tx_map.get(eid, 0),
                country_code=e.country_code,
            )
        )

    cluster_count = _count_connected_components(adjacency)
    total_connections = sum(len(v) for v in adjacency.values())
    node_count = len(nodes)

    stats = NetworkGraphStats(
        node_count=node_count,
        edge_count=len(edges),
        cluster_count=cluster_count,
        avg_connections=round(total_connections / node_count, 2) if node_count else 0.0,
    )

    logger.info(
        "network_graph_built",
        node_count=stats.node_count,
        edge_count=stats.edge_count,
        cluster_count=stats.cluster_count,
    )

    return NetworkGraphResponse(nodes=nodes, edges=edges, stats=stats)


async def get_entity_connections(
    db: AsyncSession,
    entity_id: str,
) -> EntityConnectionResponse:
    """Find all entities that a given entity has transacted with."""
    eid = uuid.UUID(entity_id)

    entity_result = await db.execute(select(Entity).where(Entity.id == eid))
    entity = entity_result.scalar_one_or_none()
    entity_name = entity.name if entity else "Unknown"

    outbound_stmt = (
        select(
            Transaction.destination_entity_id.label("other_id"),
            func.count().label("tx_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .where(
            and_(
                Transaction.source_entity_id == eid,
                Transaction.destination_entity_id.isnot(None),
            )
        )
        .group_by(Transaction.destination_entity_id)
    )
    outbound_rows = (await db.execute(outbound_stmt)).all()
    outbound_map: dict[uuid.UUID, tuple[int, float]] = {
        r.other_id: (r.tx_count, float(r.total_amount)) for r in outbound_rows
    }

    inbound_stmt = (
        select(
            Transaction.source_entity_id.label("other_id"),
            func.count().label("tx_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .where(
            and_(
                Transaction.destination_entity_id == eid,
                Transaction.source_entity_id.isnot(None),
            )
        )
        .group_by(Transaction.source_entity_id)
    )
    inbound_rows = (await db.execute(inbound_stmt)).all()
    inbound_map: dict[uuid.UUID, tuple[int, float]] = {
        r.other_id: (r.tx_count, float(r.total_amount)) for r in inbound_rows
    }

    all_connected_ids = set(outbound_map.keys()) | set(inbound_map.keys())
    if not all_connected_ids:
        return EntityConnectionResponse(
            entity_id=entity_id,
            entity_name=entity_name,
            connections=[],
        )

    connected_entities_stmt = select(Entity).where(Entity.id.in_(all_connected_ids))
    connected_entities = (await db.execute(connected_entities_stmt)).scalars().all()
    entity_lookup = {e.id: e for e in connected_entities}

    connections: list[ConnectionDetail] = []
    for cid in all_connected_ids:
        ce = entity_lookup.get(cid)
        out = outbound_map.get(cid)
        inb = inbound_map.get(cid)

        if out and inb:
            direction = "both"
            tx_count = out[0] + inb[0]
            total_amount = out[1] + inb[1]
        elif out:
            direction = "outbound"
            tx_count = out[0]
            total_amount = out[1]
        else:
            direction = "inbound"
            tx_count = inb[0] if inb else 0
            total_amount = inb[1] if inb else 0.0

        connections.append(
            ConnectionDetail(
                connected_entity_id=str(cid),
                name=ce.name if ce else "Unknown",
                type=(
                    ce.entity_type.value
                    if ce and hasattr(ce.entity_type, "value")
                    else str(ce.entity_type) if ce else "unknown"
                ),
                transaction_count=tx_count,
                total_amount=total_amount,
                direction=direction,
            )
        )

    connections.sort(key=lambda c: c.transaction_count, reverse=True)

    logger.info(
        "entity_connections_fetched",
        entity_id=entity_id,
        connection_count=len(connections),
    )

    return EntityConnectionResponse(
        entity_id=entity_id,
        entity_name=entity_name,
        connections=connections,
    )


async def analyze_network(
    db: AsyncSession,
    request: NetworkAnalysisRequest,
) -> NetworkAnalysisResponse:
    """Run network analysis: build graph, detect clusters, assess risk.

    Uses connected-component detection via BFS graph traversal.
    """
    graph = await get_network_graph(
        db,
        min_transactions=request.min_transactions,
        limit=500,
    )

    adjacency: dict[str, set[str]] = defaultdict(set)
    edge_fraud: dict[tuple[str, str], float] = {}

    for edge in graph.edges:
        adjacency[edge.source].add(edge.target)
        adjacency[edge.target].add(edge.source)
        edge_fraud[(edge.source, edge.target)] = edge.avg_fraud_score

    node_risk: dict[str, float] = {
        n.id: n.risk_score for n in graph.nodes
    }

    if request.entity_ids:
        target_ids = set(request.entity_ids)
        relevant: set[str] = set()
        for eid in target_ids:
            if eid in adjacency or eid in node_risk:
                relevant.add(eid)
                if request.include_indirect:
                    _bfs_collect(adjacency, eid, request.max_depth, relevant)
                else:
                    relevant.update(adjacency.get(eid, set()))

        filtered_adj: dict[str, set[str]] = {}
        for nid in relevant:
            if nid in adjacency:
                filtered_adj[nid] = adjacency[nid] & relevant
        adjacency = defaultdict(set, filtered_adj)

    components = _find_connected_components(adjacency)

    clusters: list[ClusterInfo] = []
    for idx, component in enumerate(components):
        scores = [node_risk.get(nid, 0.0) for nid in component]
        cluster_risk = sum(scores) / len(scores) if scores else 0.0

        edge_risks = [
            edge_fraud.get((a, b), 0.0)
            for a in component
            for b in adjacency.get(a, set())
            if (a, b) in edge_fraud
        ]
        if edge_risks:
            cluster_risk = (cluster_risk + sum(edge_risks) / len(edge_risks)) / 2.0

        clusters.append(
            ClusterInfo(
                cluster_id=idx,
                node_count=len(component),
                risk_score=round(cluster_risk, 4),
                is_suspicious=cluster_risk >= _SUSPICIOUS_FRAUD_SCORE_THRESHOLD,
                nodes=sorted(component),
            )
        )

    clusters.sort(key=lambda c: c.risk_score, reverse=True)

    risk_paths: list[RiskPath] = _find_high_risk_paths(
        adjacency, node_risk, edge_fraud
    )

    all_risks = [c.risk_score for c in clusters if c.node_count > 1]
    overall_risk = round(sum(all_risks) / len(all_risks), 4) if all_risks else 0.0

    logger.info(
        "network_analysis_complete",
        cluster_count=len(clusters),
        risk_path_count=len(risk_paths),
        overall_risk=overall_risk,
    )

    return NetworkAnalysisResponse(
        clusters=clusters,
        risk_paths=risk_paths,
        overall_risk=overall_risk,
    )


def _count_connected_components(adjacency: dict[str, set[str]]) -> int:
    """Count connected components via BFS."""
    visited: set[str] = set()
    count = 0
    for node in adjacency:
        if node not in visited:
            count += 1
            queue = [node]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                for neighbour in adjacency.get(current, set()):
                    if neighbour not in visited:
                        queue.append(neighbour)
    return count


def _find_connected_components(
    adjacency: dict[str, set[str]],
) -> list[list[str]]:
    """Return each connected component as a list of node IDs."""
    visited: set[str] = set()
    components: list[list[str]] = []

    all_nodes = set(adjacency.keys())
    for neighbors in adjacency.values():
        all_nodes.update(neighbors)

    for node in all_nodes:
        if node in visited:
            continue
        component: list[str] = []
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbour in adjacency.get(current, set()):
                if neighbour not in visited:
                    queue.append(neighbour)
        components.append(component)

    return components


def _bfs_collect(
    adjacency: dict[str, set[str]],
    start: str,
    max_depth: int,
    collected: set[str],
) -> None:
    """Collect all nodes within max_depth hops of start."""
    queue: list[tuple[str, int]] = [(start, 0)]
    visited: set[str] = set()
    while queue:
        current, depth = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        collected.add(current)
        if depth < max_depth:
            for neighbour in adjacency.get(current, set()):
                if neighbour not in visited:
                    queue.append((neighbour, depth + 1))


def _find_high_risk_paths(
    adjacency: dict[str, set[str]],
    node_risk: dict[str, float],
    edge_fraud: dict[tuple[str, str], float],
    max_paths: int = 10,
    min_path_len: int = 2,
) -> list[RiskPath]:
    """Identify short paths whose cumulative risk is above the threshold.

    Uses a bounded DFS from high-risk nodes.
    """
    high_risk_seeds = [
        nid for nid, score in node_risk.items()
        if score >= _SUSPICIOUS_FRAUD_SCORE_THRESHOLD
    ]

    paths: list[RiskPath] = []

    for seed in high_risk_seeds:
        if len(paths) >= max_paths:
            break
        stack: list[tuple[list[str], float]] = [([seed], node_risk.get(seed, 0.0))]
        while stack and len(paths) < max_paths:
            path, cumulative = stack.pop()
            current = path[-1]

            if len(path) >= min_path_len:
                avg_risk = cumulative / len(path)
                if avg_risk >= _SUSPICIOUS_FRAUD_SCORE_THRESHOLD:
                    paths.append(
                        RiskPath(path=path, risk_score=round(avg_risk, 4))
                    )
                    continue

            if len(path) >= 4:
                continue

            for neighbour in adjacency.get(current, set()):
                if neighbour not in path:
                    nr = node_risk.get(neighbour, 0.0)
                    ef = edge_fraud.get((current, neighbour), 0.0)
                    stack.append((path + [neighbour], cumulative + nr + ef))

    paths.sort(key=lambda p: p.risk_score, reverse=True)
    return paths[:max_paths]
