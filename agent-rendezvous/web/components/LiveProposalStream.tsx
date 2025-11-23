'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { ChampionIcon, Activity02Icon, Clock01Icon, Coins01Icon } from 'hugeicons-react';
import { cn } from '@/lib/utils';

interface Proposal {
  _agent: string;
  _agent_name: string;
  _score: number;
  est_cost_usd: number;
  est_latency_ms: number;
  confidence: number;
  plan: string[];
  permissions?: any;
  sandboxId?: string;
  explanation?: any;
  _goal_mismatch?: boolean;
  _telemetry?: { rtt_ms?: number };
}

interface LiveProposalStreamProps {
  proposals: Proposal[];
  isLoading: boolean;
}

export function LiveProposalStream({ proposals, isLoading }: LiveProposalStreamProps) {
  const [openIdx, setOpenIdx] = useState<number | null>(null);
  if (!isLoading && proposals.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
         <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Activity02Icon className="h-4 w-4" />
            <span>{isLoading ? 'Negotiating...' : 'Proposals Received'}</span>
            <Badge variant="secondary" className="ml-2 text-xs h-5 px-1.5 rounded-sm">
               {proposals.length}
            </Badge>
         </div>
      </div>

      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {proposals.map((prop, idx) => {
            const isWinner = idx === 0;
            return (
              <motion.div
                key={prop._agent}
                initial={{ opacity: 0, x: -20, filter: "blur(10px)" }}
                animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ 
                   type: "spring", 
                   stiffness: 500, 
                   damping: 30, 
                   delay: idx * 0.1 
                }}
                layout
              >
                <div className={cn(
                   "group relative flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg border transition-all hover:bg-muted/50",
                   isWinner ? "bg-primary/5 border-primary/20" : "bg-card/50 border-border/50"
                )}>
                   {/* Left: Agent Info */}
                   <div className="flex items-center gap-3 mb-3 sm:mb-0">
                      <div className={cn(
                         "flex h-10 w-10 items-center justify-center rounded-full text-lg font-bold",
                         isWinner ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                      )}>
                         {prop._agent_name.charAt(0)}
                      </div>
                      <div>
                         <div className="flex items-center gap-2">
                            <h4 className="font-medium text-sm">{prop._agent_name}</h4>
                            {isWinner && (
                               <Badge variant="success" className="h-4 px-1 text-[10px] gap-1">
                                  <ChampionIcon className="h-3 w-3" /> Winner
                               </Badge>
                            )}
                            {prop._goal_mismatch && (
                              <Badge variant="warning" className="h-4 px-1 text-[10px]">Goal mismatch</Badge>
                            )}
                         </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                         <span>{prop.plan.length} steps</span>
                         <span>•</span>
                         <span>{(prop.confidence * 100).toFixed(0)}% confidence</span>
                         {prop.explanation && (
                           <>
                             <span>•</span>
                             <button
                               className="text-[10px] underline underline-offset-2"
                               onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                             >
                               Why?
                             </button>
                           </>
                         )}
                         {prop.permissions && (
                           <>
                             <span>•</span>
                             {prop.permissions.fs && <Badge variant="outline" className="h-4 px-1 text-[10px]">FS</Badge>}
                             {prop.permissions.net && <Badge variant="outline" className="h-4 px-1 text-[10px]">NET</Badge>}
                             {prop.permissions.cpu && <Badge variant="outline" className="h-4 px-1 text-[10px]">CPU {prop.permissions.cpu}</Badge>}
                             {prop.permissions.ram_mb && <Badge variant="outline" className="h-4 px-1 text-[10px]">RAM {prop.permissions.ram_mb}MB</Badge>}
                             {prop.permissions.timeout_ms && <Badge variant="outline" className="h-4 px-1 text-[10px]">T/O {prop.permissions.timeout_ms}ms</Badge>}
                           </>
                         )}
                      </div>
                   </div>
                   </div>

                   {/* Right: Metrics */}
                   <div className="flex items-center gap-4 sm:gap-6 w-full sm:w-auto justify-between sm:justify-end">
                      <div className="flex flex-col items-end">
                         <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-0.5">
                            <Coins01Icon className="h-3 w-3" /> Cost
                         </div>
                         <span className="font-mono text-sm">${prop.est_cost_usd.toFixed(4)}</span>
                      </div>
                      
                      <div className="flex flex-col items-end">
                         <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-0.5">
                            <Clock01Icon className="h-3 w-3" /> Latency
                         </div>
                         <span className="font-mono text-sm">{prop.est_latency_ms}ms</span>
                         {prop._telemetry?.rtt_ms != null && (
                           <Badge variant="outline" className="mt-1 h-4 px-1 text-[10px]">RTT {prop._telemetry.rtt_ms}ms</Badge>
                         )}
                      </div>

                      <div className="flex flex-col items-end pl-2 border-l border-white/5">
                         <span className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">Score</span>
                         <span className={cn(
                            "font-mono font-bold text-lg",
                            isWinner ? "text-primary" : "text-foreground"
                         )}>
                            {prop._score.toFixed(2)}
                         </span>
                      </div>
                   </div>
                   
                   {/* Absolute Glow for Winner */}
                   {isWinner && (
                      <div className="absolute inset-0 rounded-lg bg-primary/5 pointer-events-none animate-pulse" />
                   )}
                </div>
                {openIdx === idx && prop.explanation && (
                  <div className="mt-2 p-3 rounded-lg border bg-background/40">
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {(() => {
                        const peer = proposals[(idx === 0 ? 1 : 0)] as any;
                        const hasPeer = Boolean(peer);
                        const scoreDelta = hasPeer ? (prop._score - peer._score) : undefined;
                        const costDelta = hasPeer ? (prop.est_cost_usd - peer.est_cost_usd) : undefined;
                        const latDelta = hasPeer ? (prop.est_latency_ms - peer.est_latency_ms) : undefined;
                        const budgetMax = prop.explanation.constraints?.budget_max_usd ?? null;
                        const deadlineMs = prop.explanation.constraints?.sla_deadline_ms ?? null;
                        const cost = prop.explanation.inputs?.cost_usd ?? prop.est_cost_usd;
                        const latency = prop.explanation.inputs?.latency_ms ?? prop.est_latency_ms;
                        const budgetHeadroom = budgetMax != null ? (budgetMax - cost) : null;
                        const timeHeadroom = deadlineMs != null ? (deadlineMs - latency) : null;
                        return (
                          <>
                            {hasPeer && (
                              <>
                                <div className="flex justify-between"><span>Score lead vs {peer._agent_name}</span><span className="font-mono">{(scoreDelta as number).toFixed(2)}</span></div>
                                <div className="flex justify-between"><span>Cost Δ vs {peer._agent_name}</span><span className="font-mono">{(costDelta as number).toFixed(4)}</span></div>
                                <div className="flex justify-between"><span>Latency Δ vs {peer._agent_name}</span><span className="font-mono">{(latDelta as number)}ms</span></div>
                              </>
                            )}
                            {budgetHeadroom != null && (
                              <div className="flex justify-between"><span>Budget headroom</span><span className="font-mono">{budgetHeadroom.toFixed(4)} USD</span></div>
                            )}
                            {timeHeadroom != null && (
                              <div className="flex justify-between"><span>Deadline headroom</span><span className="font-mono">{timeHeadroom} ms</span></div>
                            )}
                          </>
                        );
                      })()}
                    </div>
                    {Array.isArray(prop.plan) && prop.plan.length > 0 && (
                      <div className="mt-2 text-xs">
                        <div className="mb-1 text-muted-foreground">Plan preview</div>
                        <ul className="list-disc list-inside">
                          {prop.plan.slice(0, 2).map((s, i) => (
                            <li key={i} className="font-mono">{s}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {Array.isArray(prop.explanation.notes) && (
                      <ul className="mt-2 list-disc list-inside text-[10px] text-muted-foreground">
                        {prop.explanation.notes.map((n: string, i: number) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    )}
                    <div className="mt-2 text-[10px] text-muted-foreground">Formula: {prop.explanation.formula}</div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
