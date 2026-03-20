"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { NetworkNode, NetworkEdge } from "@/types/network";
import { NodeTooltip } from "./node-tooltip";

interface SimNode extends NetworkNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

interface GraphCanvasProps {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  onNodeClick?: (node: NetworkNode) => void;
  width?: number;
  height?: number;
}

const RISK_COLORS: Record<string, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

const REPULSION = 5000;
const ATTRACTION = 0.005;
const CENTER_GRAVITY = 0.01;
const DAMPING = 0.85;
const MIN_RADIUS = 8;
const MAX_RADIUS = 30;

function nodeRadius(txCount: number, maxTxCount: number): number {
  if (maxTxCount <= 0) return MIN_RADIUS;
  const t = Math.min(txCount / maxTxCount, 1);
  return MIN_RADIUS + t * (MAX_RADIUS - MIN_RADIUS);
}

function distance(a: { x: number; y: number }, b: { x: number; y: number }) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy);
}

export function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
  width: propWidth,
  height: propHeight,
}: GraphCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simNodesRef = useRef<SimNode[]>([]);
  const animFrameRef = useRef<number>(0);

  const [canvasSize, setCanvasSize] = useState({ w: propWidth ?? 800, h: propHeight ?? 600 });
  const [tooltip, setTooltip] = useState<{
    node: NetworkNode | null;
    position: { x: number; y: number };
    visible: boolean;
  }>({ node: null, position: { x: 0, y: 0 }, visible: false });

  const dragRef = useRef<{ nodeIndex: number; offsetX: number; offsetY: number } | null>(null);
  const panRef = useRef({ offsetX: 0, offsetY: 0 });
  const isPanningRef = useRef(false);
  const panStartRef = useRef({ x: 0, y: 0, ox: 0, oy: 0 });
  const zoomRef = useRef(1);

  const edgeLookupRef = useRef<Map<string, Map<string, NetworkEdge>>>(new Map());

  useEffect(() => {
    const lookup = new Map<string, Map<string, NetworkEdge>>();
    for (const e of edges) {
      if (!lookup.has(e.source)) lookup.set(e.source, new Map());
      lookup.get(e.source)!.set(e.target, e);
    }
    edgeLookupRef.current = lookup;
  }, [edges]);

  useEffect(() => {
    if (propWidth && propHeight) {
      setCanvasSize({ w: propWidth, h: propHeight });
      return;
    }
    const container = containerRef.current;
    if (!container) return;

    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setCanvasSize({
          w: entry.contentRect.width,
          h: entry.contentRect.height,
        });
      }
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, [propWidth, propHeight]);

  useEffect(() => {
    const maxTx = Math.max(1, ...nodes.map((n) => n.transaction_count));
    const cx = canvasSize.w / 2;
    const cy = canvasSize.h / 2;

    const existing = new Map<string, SimNode>();
    for (const sn of simNodesRef.current) {
      existing.set(sn.id, sn);
    }

    simNodesRef.current = nodes.map((n, i) => {
      const prev = existing.get(n.id);
      const angle = (2 * Math.PI * i) / nodes.length;
      const spread = Math.min(canvasSize.w, canvasSize.h) * 0.3;
      return {
        ...n,
        x: prev ? prev.x : cx + Math.cos(angle) * spread + (Math.random() - 0.5) * 40,
        y: prev ? prev.y : cy + Math.sin(angle) * spread + (Math.random() - 0.5) * 40,
        vx: prev ? prev.vx : 0,
        vy: prev ? prev.vy : 0,
        radius: nodeRadius(n.transaction_count, maxTx),
      };
    });

    panRef.current = { offsetX: 0, offsetY: 0 };
    zoomRef.current = 1;
  }, [nodes, canvasSize.w, canvasSize.h]);

  const screenToWorld = useCallback(
    (sx: number, sy: number) => ({
      x: (sx - panRef.current.offsetX) / zoomRef.current,
      y: (sy - panRef.current.offsetY) / zoomRef.current,
    }),
    []
  );

  const findNodeAt = useCallback(
    (sx: number, sy: number): number => {
      const { x, y } = screenToWorld(sx, sy);
      const simNodes = simNodesRef.current;
      for (let i = simNodes.length - 1; i >= 0; i--) {
        const n = simNodes[i];
        if (distance(n, { x, y }) <= n.radius) return i;
      }
      return -1;
    },
    [screenToWorld]
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      const idx = findNodeAt(sx, sy);

      if (idx >= 0) {
        const { x, y } = screenToWorld(sx, sy);
        const n = simNodesRef.current[idx];
        dragRef.current = { nodeIndex: idx, offsetX: n.x - x, offsetY: n.y - y };
      } else {
        isPanningRef.current = true;
        panStartRef.current = {
          x: e.clientX,
          y: e.clientY,
          ox: panRef.current.offsetX,
          oy: panRef.current.offsetY,
        };
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      if (dragRef.current) {
        const { x, y } = screenToWorld(sx, sy);
        const n = simNodesRef.current[dragRef.current.nodeIndex];
        n.x = x + dragRef.current.offsetX;
        n.y = y + dragRef.current.offsetY;
        n.vx = 0;
        n.vy = 0;
        return;
      }

      if (isPanningRef.current) {
        panRef.current.offsetX =
          panStartRef.current.ox + (e.clientX - panStartRef.current.x);
        panRef.current.offsetY =
          panStartRef.current.oy + (e.clientY - panStartRef.current.y);
        return;
      }

      const idx = findNodeAt(sx, sy);
      if (idx >= 0) {
        canvas.style.cursor = "pointer";
        setTooltip({
          node: simNodesRef.current[idx],
          position: { x: e.clientX, y: e.clientY },
          visible: true,
        });
      } else {
        canvas.style.cursor = "default";
        setTooltip((prev) => (prev.visible ? { ...prev, visible: false } : prev));
      }
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (dragRef.current) {
        const rect = canvas.getBoundingClientRect();
        const sx = e.clientX - rect.left;
        const sy = e.clientY - rect.top;
        const idx = findNodeAt(sx, sy);
        if (idx === dragRef.current.nodeIndex && onNodeClick) {
          onNodeClick(simNodesRef.current[idx]);
        }
      }
      dragRef.current = null;
      isPanningRef.current = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      const oldZoom = zoomRef.current;
      const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
      const newZoom = Math.max(0.1, Math.min(5, oldZoom * factor));

      panRef.current.offsetX = mx - ((mx - panRef.current.offsetX) / oldZoom) * newZoom;
      panRef.current.offsetY = my - ((my - panRef.current.offsetY) / oldZoom) * newZoom;
      zoomRef.current = newZoom;
    };

    canvas.addEventListener("mousedown", handleMouseDown);
    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseup", handleMouseUp);
    canvas.addEventListener("mouseleave", () => {
      dragRef.current = null;
      isPanningRef.current = false;
      setTooltip((prev) => (prev.visible ? { ...prev, visible: false } : prev));
    });
    canvas.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      canvas.removeEventListener("mousedown", handleMouseDown);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseup", handleMouseUp);
      canvas.removeEventListener("wheel", handleWheel);
    };
  }, [findNodeAt, screenToWorld, onNodeClick]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const nodeById = new Map<string, number>();

    const tick = () => {
      const simNodes = simNodesRef.current;
      const cx = canvasSize.w / 2;
      const cy = canvasSize.h / 2;

      nodeById.clear();
      for (let i = 0; i < simNodes.length; i++) {
        nodeById.set(simNodes[i].id, i);
      }

      for (let i = 0; i < simNodes.length; i++) {
        const a = simNodes[i];
        for (let j = i + 1; j < simNodes.length; j++) {
          const b = simNodes[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 1) {
            dx = (Math.random() - 0.5) * 2;
            dy = (Math.random() - 0.5) * 2;
            dist = 1;
          }
          const force = REPULSION / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx += fx;
          a.vy += fy;
          b.vx -= fx;
          b.vy -= fy;
        }
      }

      for (const edge of edges) {
        const ai = nodeById.get(edge.source);
        const bi = nodeById.get(edge.target);
        if (ai === undefined || bi === undefined) continue;
        const a = simNodes[ai];
        const b = simNodes[bi];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 1) continue;
        const force = dist * ATTRACTION * edge.weight;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }

      for (const n of simNodes) {
        if (dragRef.current && simNodes[dragRef.current.nodeIndex] === n) continue;
        n.vx += (cx - n.x) * CENTER_GRAVITY;
        n.vy += (cy - n.y) * CENTER_GRAVITY;
        n.vx *= DAMPING;
        n.vy *= DAMPING;
        n.x += n.vx;
        n.y += n.vy;
      }

      const dpr = window.devicePixelRatio || 1;
      canvas.width = canvasSize.w * dpr;
      canvas.height = canvasSize.h * dpr;
      canvas.style.width = `${canvasSize.w}px`;
      canvas.style.height = `${canvasSize.h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      ctx.clearRect(0, 0, canvasSize.w, canvasSize.h);
      ctx.save();
      ctx.translate(panRef.current.offsetX, panRef.current.offsetY);
      ctx.scale(zoomRef.current, zoomRef.current);

      for (const edge of edges) {
        const ai = nodeById.get(edge.source);
        const bi = nodeById.get(edge.target);
        if (ai === undefined || bi === undefined) continue;
        const a = simNodes[ai];
        const b = simNodes[bi];

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.lineWidth = Math.max(0.5, Math.min(edge.weight * 0.5, 4));

        if (edge.is_suspicious) {
          ctx.strokeStyle = "rgba(239, 68, 68, 0.6)";
          ctx.setLineDash([6, 4]);
        } else {
          ctx.strokeStyle = "rgba(156, 163, 175, 0.4)";
          ctx.setLineDash([]);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      }

      for (const n of simNodes) {
        const color = RISK_COLORS[n.risk_level] ?? "#6b7280";

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.85;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();

        const fontSize = Math.max(9, Math.min(12, n.radius * 0.8));
        ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
        ctx.fillStyle = "#374151";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(n.label, n.x, n.y + n.radius + 4, 100);
      }

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [edges, canvasSize]);

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden">
      <canvas ref={canvasRef} className="block h-full w-full" />
      <NodeTooltip
        node={tooltip.node}
        position={tooltip.position}
        visible={tooltip.visible}
      />
    </div>
  );
}
