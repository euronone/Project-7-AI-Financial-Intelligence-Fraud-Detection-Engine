export interface NetworkNode {
  id: string;
  label: string;
  entity_type: string;
  risk_score: number;
  risk_level: string;
  alert_count: number;
  transaction_count: number;
  country_code: string | null;
}

export interface NetworkEdge {
  source: string;
  target: string;
  weight: number;
  total_amount: number;
  avg_fraud_score: number;
  is_suspicious: boolean;
}

export interface NetworkGraphStats {
  node_count: number;
  edge_count: number;
  cluster_count: number;
  avg_connections: number;
}

export interface NetworkGraphResponse {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  stats: NetworkGraphStats;
}

export interface ConnectionDetail {
  connected_entity_id: string;
  name: string;
  type: string;
  transaction_count: number;
  total_amount: number;
  direction: "inbound" | "outbound" | "both";
}

export interface EntityConnectionResponse {
  entity_id: string;
  entity_name: string;
  connections: ConnectionDetail[];
}
