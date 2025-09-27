// D3ForceSpringGraph.jsx
// A reusable React + D3 force (spring) network component tailored for Neo4j-style data
// - Responsive: resizes with its container
// - Zoom & pan: mousewheel/drag to explore
// - Drag nodes: click-drag nodes to reposition
// - Tooltip: hover nodes or links to see details
// - Works with typical Neo4j JSON (nodes with id/labels/properties, links with source/target/type/properties)
//
// Usage:
// <div style={{height: 600}}>
//   <D3ForceSpringGraph data={sampleNeo4jData} />
// </div>
//
// Props:
// - data: { nodes: Node[], links: Link[] }
// - height: number (optional; if not given, uses container height)
// - charge: number (default -180)
// - linkDistance: number | (link)=>number (default 80)
// - collideRadius: number (default 24)
// - onNodeClick, onLinkClick: callbacks
// - nodeLabel: (node)=>string (defaults to node.properties?.name || node.id)
// - linkLabel: (link)=>string (defaults to link.type)
//
// Exported: sampleData (a small example matching Neo4j-ish shape)

import React, { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";

export const sampleData = {
    nodes: [
        { id: "doc:A", labels: ["Document"], properties: { name: "Report A", year: 2023 } },
        { id: "doc:B", labels: ["Document"], properties: { name: "Report B", year: 2024 } },
        { id: "equip:jaw_crusher", labels: ["Equipment"], properties: { name: "Jaw Crusher", capacity: "400–1000 tph" } },
        { id: "equip:ball_mill", labels: ["Equipment"], properties: { name: "Ball Mill", power: "2 MW" } },
        { id: "mat:ore", labels: ["Material"], properties: { name: "Ore", grade: "1.8 g/t Au" } },
        { id: "proc:crushing", labels: ["Process"], properties: { name: "Crushing" } },
        { id: "proc:milling", labels: ["Process"], properties: { name: "Milling" } },
    ],
    links: [
        { source: "doc:A", target: "equip:jaw_crusher", type: "MENTIONS" },
        { source: "doc:B", target: "equip:ball_mill", type: "MENTIONS" },
        { source: "proc:crushing", target: "equip:jaw_crusher", type: "USES", properties: { cost_per_ton: 1.2 } },
        { source: "proc:milling", target: "equip:ball_mill", type: "USES", properties: { cost_per_ton: 2.6 } },
        { source: "mat:ore", target: "proc:crushing", type: "FEEDS" },
        { source: "proc:crushing", target: "proc:milling", type: "NEXT" },
    ],
};

const defaultNodeLabel = (n) => n?.properties?.name ?? String(n?.id ?? "");
const defaultLinkLabel = (l) => l?.type ?? "";

const NODE_TYPES = [
    "Equipment",
    "Material",
    "Process",
    "Project",
    "Scenario",
    "Other",
];

// Predefined color map for node types
const NODE_TYPE_COLORS = {
    // Costrule: "#e377c2", // Pink
    Equipment: "#1f77b4", // Blue
    Material: "#ff7f0e", // Orange
    Other: "#7f7f7f", // Gray
    Process: "#2ca02c", // Green
    Provenance: "#d62728", // Red
    Scenario: "#9467bd", // Purple
    Project: "#8c564b", // Brown
};

// Fallback color for unknown types
const DEFAULT_COLOR = NODE_TYPE_COLORS.Other; // Use "Other" as the default color

export default function D3ForceSpringGraph({
    data,
    height,
    width,
    charge = -550,
    linkDistance = 350,
    collideRadius = 50,
    onNodeClick,
    onLinkClick,
    nodeLabel = defaultNodeLabel,
    linkLabel = defaultLinkLabel,
}) {
    const containerRef = useRef(null);
    const svgRef = useRef(null);
    const gRef = useRef(null);
    const tooltipRef = useRef(null);
    const simulationRef = useRef(null);
    const [dims, setDims] = useState({ width: 800, height: 500 });

    // Clone input so D3 can mutate positions without clobbering props
    const { nodes, links } = useMemo(() => ({
        nodes: data?.graph?.nodes ? data.graph.nodes.map((d) => ({ ...d })) : [],
        links: data?.graph?.links ? data.graph.links.map((l) => ({ ...l })) : [],
    }), [data]);

    const color = useMemo(() => {
        return (label) => NODE_TYPE_COLORS[label] || DEFAULT_COLOR;
    }, []);

    // Build quick neighbor lookup for highlighting
    const neighbor = useMemo(() => {
        const m = new Map();
        links.forEach((l) => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            if (!m.has(s)) m.set(s, new Set());
            if (!m.has(t)) m.set(t, new Set());
            m.get(s).add(t);
            m.get(t).add(s);
        });
        return m;
    }, [links]);

    // Responsive sizing
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const ro = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const cr = entry.contentRect;
                setDims({ width: width ?? Math.max(300, cr.width), height: height ?? Math.max(300, cr.height) });
            }
        });
        ro.observe(el);
        return () => ro.disconnect();
    }, [height, width]);

    // Initialize SVG scaffold once
    useEffect(() => {
        const svg = d3.select(svgRef.current);
        const g = d3.select(gRef.current);

        // Define arrowheads
        const defs = svg.append("defs");
        defs
            .append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 18)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // Zoom + pan
        const zoomed = (event) => {
            g.attr("transform", event.transform);
        };
        svg.call(
            d3
                .zoom()
                .scaleExtent([0.1, 8])
                .on("zoom", zoomed)
        );

        // Tooltip (HTML overlay)
        const tooltip = d3
            .select(containerRef.current)
            .append("div")
            .attr("class", "pointer-events-none select-none text-xs px-3 py-2 rounded-md shadow hidden absolute z-10")
            .style("max-width", "350px")
            .style("padding", "6px 12px")
            .style("background", "rgba(255,255,255,0.925)") // semi-transparent dark background
            .style("color", "#333")
            .style("top", "12px")
            .style("right", "12px")
            .style("border-radius", "8px")
            .style("border", "1px solid rgba(0,0,0,0.1)")
            .style("left", null)
            .style("position", "absolute");

        tooltipRef.current = tooltip.node();

        return () => {
            d3.select(tooltipRef.current)?.remove();
        };
    }, []);

    // Build/Update the graph when data or dims change
    useEffect(() => {
        const width = dims.width;
        const height = dims.height;
        const svg = d3.select(svgRef.current);
        const g = d3.select(gRef.current);

        svg.attr("viewBox", [0, 0, width, height]).attr("width", width).attr("height", height);

        // --- JOIN: Links
        const link = g
            .selectAll("line.link")
            .data(links, (d) => `${typeof d.source === "object" ? d.source.id : d.source}|${typeof d.target === "object" ? d.target.id : d.target}|${d.type ?? ''}`);

        link.exit().remove();

        const linkEnter = link
            .enter()
            .append("line")
            .attr("class", "link")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", (d) => Math.max(1, d.value || 1))
            .attr("marker-end", "url(#arrow)");

        const linkSel = linkEnter.merge(link);

        // --- JOIN: Link labels (optional; show on strong zoom)
        const linkText = g
            .selectAll("text.link-label")
            .data(links, (d) => `t|${typeof d.source === "object" ? d.source.id : d.source}|${typeof d.target === "object" ? d.target.id : d.target}|${d.type ?? ''}`);

        linkText.exit().remove();

        const linkTextEnter = linkText
            .enter()
            .append("text")
            .attr("class", "link-label fill-gray-600 text-[10px]")
            .attr("dy", -2)
            .text((d) => linkLabel(d));

        const linkTextSel = linkTextEnter.merge(linkText);

        // --- JOIN: Nodes
        const node = g
            .selectAll("g.node")
            .data(nodes, (d) => d.id);

        node.exit().remove();

        const nodeEnter = node
            .enter()
            .append("g")
            .attr("class", "node cursor-grab");

        nodeEnter
            .append("circle")
            .attr("r", 8)
            .attr("fill", (d) => color((d.labels && d.labels[0]) || "Other"))
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5);

        nodeEnter
            .append("text")
            .attr("class", "node-label text-xs fill-gray-800")
            .attr("x", 10)
            .attr("y", 4)
            .text((d) => nodeLabel(d));

        const nodeSel = nodeEnter.merge(node);

        // Hover + tooltip handlers
        const showTooltip = (html) => {
            const el = d3.select(tooltipRef.current);
            el.html(html)
                .style("position", "absolute")
                .style("top", "24px")
                .style("right", "24px")
                .style("left", null)
                .classed("hidden", false);
        };
        const hideTooltip = () => d3.select(tooltipRef.current).classed("hidden", true);

        const nodeHTML = (d) => {
            const header = `<div class='font-semibold mb-1' style="background-color: lightblue; padding: 6px; border-radius: 5px; border: 1px solid red; font-weight: 500">Label: ${nodeLabel(d)}</div>`;
            const labels = d.labels?.length ? `<div class='mb-1 opacity-80' style="color: navy; padding: 6px; border-radius: 5px; border: 1px solid navy; font-weight: 600;">${d.labels.join(", ")}</div>` : "";
            const props = d.properties ?
                `<div class='grid grid-cols-[auto_1fr] gap-x-2 gap-y-1'>${Object.entries(d.properties)
                    .map(([k, v]) => `<div class='opacity-70'><b>${k}</b>:${String(v)}</div>`)
                    .join("")}</div>` : "";
            return `<div style="display: flex; gap: 10px; align-items: center;">${labels} - ${header}</div>${props}`;
        };

        const linkHTML = (l) => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            const header = `<div class='font-semibold mb-1' style="color: navy; padding: 3px; border-radius: 5px; border: 1px solid navy; font-weight: 600">${linkLabel(l)}</div>`;
            // const header = `<div class='font-semibold mb-1'>${linkLabel(l)}</div>`;
            const ends = `<div class='opacity-80 text-[11px]'>${s} → ${t}</div>`;
            const props = l.properties ?
                `<div class='grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 mt-1'>${Object.entries(l.properties)
                    .map(([k, v]) => `<div class='opacity-70'>${k}</div><div class='break-words'>${String(v)}</div>`)
                    .join("")}</div>` : "";
            return `${header}${ends}${props}`;
        };

        nodeSel
            .on("mouseenter", function (event, d) {
                d3.select(this).select("circle").transition().duration(120).attr("r", 13).attr("stroke-width", 2);
                // Fade non-neighbors
                g.selectAll("g.node").classed("opacity-30", (o) => o.id !== d.id && !neighbor.get(d.id)?.has(o.id));
                g.selectAll("line.link").classed("opacity-20", (l) => l.source.id !== d.id && l.target.id !== d.id);
                showTooltip(nodeHTML(d));
            })
            .on("mouseleave", function () {
                d3.select(this).select("circle").transition().duration(120).attr("r", 8).attr("stroke-width", 1.5);
                g.selectAll("g.node").classed("opacity-30", false);
                g.selectAll("line.link").classed("opacity-20", false);
                hideTooltip();
            })
            .on("click", (event, d) => onNodeClick?.(d));

        linkSel
            .on("mouseenter", function (event, l) {
                d3.select(this).attr("stroke-opacity", 1).attr("stroke-width", (d) => Math.max(4, (d.value || 1) + 1));
                showTooltip(linkHTML(l));
            })
            .on("mouseleave", function () {
                d3.select(this).attr("stroke-opacity", 0.6).attr("stroke-width", (d) => Math.max(1, d.value || 1));
                hideTooltip();
            })
            .on("click", (event, l) => onLinkClick?.(l));

        // Drag behavior
        const drag = d3
            .drag()
            .on("start", (event, d) => {
                if (!event.active) simulationRef.current.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
                d3.select(event.sourceEvent?.target?.closest("g.node"))?.classed("cursor-grabbing", true);
            })
            .on("drag", (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) simulationRef.current.alphaTarget(0);
                d.fx = null;
                d.fy = null;
                d3.select(event.sourceEvent?.target?.closest("g.node"))?.classed("cursor-grabbing", false);
            });

        nodeSel.call(drag);

        // Simulation
        const sim = (simulationRef.current ||= d3.forceSimulation());

        sim
            .nodes(nodes)
            .force(
                "link",
                d3
                    .forceLink(links)
                    .id((d) => d.id)
                    .distance(typeof linkDistance === "function" ? linkDistance : () => linkDistance)
                    .strength(0.9)
            )
            .force("charge", d3.forceManyBody().strength(charge))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide(collideRadius))
            .alpha(2.75)
            .alphaDecay(0.025)
            .on("tick", ticked);

        sim.force("center").x(width / 2).y(height / 2);

        function ticked() {
            linkSel
                .attr("x1", (d) => d.source.x)
                .attr("y1", (d) => d.source.y)
                .attr("x2", (d) => d.target.x)
                .attr("y2", (d) => d.target.y);

            linkTextSel
                .attr("x", (d) => (d.source.x + d.target.x) / 2)
                .attr("y", (d) => (d.source.y + d.target.y) / 2)
                .attr("display", () => (d3.zoomTransform(svgRef.current).k > 1.5 ? null : "none"));

            nodeSel.attr("transform", (d) => `translate(${d.x},${d.y})`);
        }

        return () => {
            // do not stop the sim entirely across renders; but clear listeners to avoid piling up
            sim.on("tick", null);
        };
    }, [nodes, links, dims, charge, linkDistance, collideRadius, nodeLabel, linkLabel, onNodeClick, onLinkClick, neighbor]);

    const legendLabels = useMemo(() => {
        // Get unique labels from nodes
        return Array.from(new Set(nodes.flatMap((n) => n.labels ?? ["Other"])));
    }, [nodes]);

    const legendColors = useMemo(() => {
        return NODE_TYPES.map((label) => ({
            label,
            color: color(label),
        }));
    }, [color]);

    return (
        <div
            ref={containerRef}
            className="relative w-full h-full bg-white rounded-2xl shadow-inner"
            style={{
                backgroundColor: "#fafbff",
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                justifyContent: "flex-start",
                position: "relative",
            }}
        >
            {/* Legend */}
            <div
                style={{
                    position: "absolute",
                    top: 16,
                    left: 16,
                    zIndex: 20,
                    background: "#f5f5f5",
                    borderRadius: 8,
                    boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
                    padding: "8px 12px",
                    fontSize: 13,
                    minWidth: 120,
                }}
            >
                <div style={{ fontWeight: 600, marginBottom: 4 }}>Legend</div>
                {legendColors.map(({ label, color }) => (
                    <div key={label} style={{ display: "flex", alignItems: "center", marginBottom: 2 }}>
                        <span
                            style={{
                                display: "inline-block",
                                width: 14,
                                height: 14,
                                borderRadius: "50%",
                                background: color,
                                marginRight: 8,
                                border: "1px solid #ccc",
                            }}
                        />
                        <span>{label}</span>
                    </div>
                ))}
            </div>
            <svg ref={svgRef} className="block w-full h-full">
                <g ref={gRef} />
            </svg>
        </div>
    );
}