"use client";

import * as React from 'react';
import { useEffect, useState } from 'react';
import { Link01Icon } from 'hugeicons-react';
import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';

export function Header() {
  const [agents, setAgents] = useState<any[]>([]);
  const [trace, setTrace] = useState<any>(null);
  const hubUrl = process.env.NEXT_PUBLIC_HUB_URL || 'http://localhost:8000';
  useEffect(() => {
    const ac = new AbortController();
    const load = async () => {
      try {
        const res = await fetch(`${hubUrl}/agents`, { signal: ac.signal });
        if (!res.ok) return;
        const data = await res.json();
        setAgents(data);
      } catch {}
    };
    load();
    return () => ac.abort();
  }, [hubUrl]);
  const refreshTrace = async () => {
    try {
      const res = await fetch(`${hubUrl}/orchestrate/trace`);
      if (!res.ok) return;
      const data = await res.json();
      setTrace(data);
    } catch {}
  };
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/60 backdrop-blur-xl supports-[backdrop-filter]:bg-background/30">
      <div className="container mx-auto flex h-14 items-center justify-between px-4 md:px-6 lg:px-8 max-w-6xl">
        <motion.div
          className="flex items-center gap-2"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10">
             <Link01Icon className="h-4 w-4 text-foreground" />
          </div>
          <h1 className="font-serif text-xl font-medium tracking-tight text-foreground">
            AgentBridge
          </h1>
        </motion.div>
        
        <div className="flex items-center gap-4">
          <nav className="flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <LinkItem href="#" label="Marketplace" delay={0.1} />
            <LinkItem href="#" label="Agents" delay={0.2} />
            <LinkItem href="#" label="History" delay={0.3} />
          </nav>
          {process.env.NODE_ENV !== 'production' && (
            <Sheet>
              <SheetTrigger asChild>
                <motion.button
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="rounded-md"
                >
                  <Badge variant="outline" className="text-[10px] px-2 py-0.5">Dev Diagnostics</Badge>
                </motion.button>
              </SheetTrigger>
              <SheetContent side="right" className="w-80">
                <SheetHeader>
                  <SheetTitle>Diagnostics</SheetTitle>
                  <SheetDescription>Development tools</SheetDescription>
                </SheetHeader>
                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span>Environment</span>
                    <Badge variant="outline" className="text-[10px]">{process.env.NODE_ENV}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Hub URL</span>
                    <Badge variant="outline" className="text-[10px]">{hubUrl}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Agents</span>
                    <Badge variant="outline" className="text-[10px]">{agents.length}</Badge>
                  </div>
                  <div className="max-h-32 overflow-y-auto space-y-1 border rounded-md p-2 bg-muted/20">
                    {agents.map((a: any) => (
                      <div key={a.id} className="flex justify-between items-center">
                        <span className="font-medium truncate max-w-[150px]" title={a.name}>{a.name}</span>
                        <Badge variant="outline" className="text-[10px]">{a.id}</Badge>
                      </div>
                    ))}
                    {agents.length === 0 && (
                      <div className="text-xs text-muted-foreground">Loading agents...</div>
                    )}
                  </div>
                  <div className="mt-4">
                    <div className="flex justify-between items-center">
                      <span>Last Orchestrator Trace</span>
                      <button onClick={refreshTrace} className="text-xs underline">Refresh</button>
                    </div>
                    {trace?.data ? (
                      <div className="mt-2 space-y-2">
                        <div className="flex justify-between items-center">
                          <span>Winner</span>
                          <Badge variant="outline" className="text-[10px]">{trace.data.winner_name || trace.data.winner || '—'}</Badge>
                        </div>
                        <div className="rounded-md border bg-background/40 p-2 max-h-40 overflow-auto">
                          {Array.isArray(trace.data.trace) && trace.data.trace.map((t: any, i: number) => (
                            <div key={i} className="text-[10px] text-muted-foreground flex justify-between">
                              <span className="truncate max-w-[140px]">{t.event}</span>
                              <span>{t.count ?? t.agent ?? ''}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground mt-2">No trace yet</div>
                    )}
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          )}
        </div>
      </div>
    </header>
  );
}

function LinkItem({ href, label, delay }: { href: string; label: string; delay: number }) {
  return (
    <motion.a 
      href={href}
      className="hover:text-foreground transition-colors"
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
    >
      {label}
    </motion.a>
  )
}
