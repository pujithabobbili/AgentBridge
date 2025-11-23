'use client';

import { useEffect, useState, useRef, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useTheme } from 'next-themes';

// @ts-ignore
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-full text-muted-foreground">Loading visualization...</div>
});

interface AgentGraphProps {
    intent: string;
    agents?: any[];
    active?: boolean;
}

export function AgentGraph({ intent, agents = [], active = false }: AgentGraphProps) {
    const { theme } = useTheme();
    const fgRef = useRef<any>(null);
    const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });

    // Mock agent data if none provided, to show a rich graph
    const mockAgents = useMemo(() => [
        { id: 'agent-1', name: 'TravelAgent', group: 'agent', color: '#4ade80' },
        { id: 'agent-2', name: 'SearchAgent', group: 'agent', color: '#60a5fa' },
        { id: 'agent-3', name: 'CodeAgent', group: 'agent', color: '#f472b6' },
        { id: 'agent-4', name: 'DataAgent', group: 'agent', color: '#a78bfa' },
        { id: 'agent-5', name: 'WriterAgent', group: 'agent', color: '#fbbf24' },
        { id: 'agent-6', name: 'PlannerAgent', group: 'agent', color: '#2dd4bf' },
        { id: 'agent-7', name: 'ReviewAgent', group: 'agent', color: '#f87171' },
        { id: 'agent-8', name: 'SecurityAgent', group: 'agent', color: '#94a3b8' },
    ], []);

    useEffect(() => {
        if (!active) return;

        // Initial state: just the user intent
        const nodes: any[] = [{ id: 'user', name: 'User Intent', group: 'user', val: 20, color: '#ffffff' }];
        const links: any[] = [];

        setGraphData({ nodes, links });

        // Simulate agents appearing and connecting
        let timer: NodeJS.Timeout;
        let step = 0;

        const animateGraph = () => {
            if (step >= mockAgents.length) return;

            const currentStep = step;

            setGraphData(prev => {
                const newNodes = [...prev.nodes];
                const newLinks = [...prev.links];

                // Add a few agents at a time or one by one
                const agent = mockAgents[currentStep];
                if (!agent) return prev;

                newNodes.push({ ...agent, val: 10 });
                newLinks.push({ source: 'user', target: agent.id });

                return { nodes: newNodes, links: newLinks };
            });

            step++;
            timer = setTimeout(animateGraph, 500); // Add a new agent every 500ms
        };

        // Start animation after a short delay
        timer = setTimeout(animateGraph, 500);

        return () => clearTimeout(timer);
    }, [active, intent, mockAgents]);

    return (
        <div className="h-[400px] w-full rounded-lg overflow-hidden border bg-slate-950 relative">
            {active && (
                // @ts-ignore
                <ForceGraph3D
                    ref={fgRef}
                    graphData={graphData}
                    nodeLabel="name"
                    nodeColor="color"
                    nodeVal="val"
                    linkColor={() => '#ffffff40'}
                    linkWidth={1}
                    linkDirectionalParticles={2}
                    linkDirectionalParticleSpeed={0.005}
                    linkDirectionalParticleWidth={2}
                    backgroundColor="#020617" // slate-950
                    showNavInfo={false}
                    enableNodeDrag={false}
                    // interactions handled by library defaults
                    onEngineStop={() => fgRef.current?.zoomToFit(400)}
                />
            )}
            <div className="absolute bottom-4 left-4 text-xs text-slate-400 pointer-events-none">
                <p>Visualizing Agent Network...</p>
            </div>
        </div>
    );
}
