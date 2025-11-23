'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { TaskTemplateSelector } from '@/components/TaskTemplateSelector';
import { TaskHistory } from '@/components/TaskHistory';
import { FileUpload } from '@/components/FileUpload';
import { LiveProposalStream } from '@/components/LiveProposalStream';
import { Header } from '@/components/layout/Header';
import { PageShell } from '@/components/layout/PageShell';
import {
  Loading03Icon,
  AlertCircleIcon,
  CheckmarkCircle02Icon,
  SparklesIcon,
  Globe02Icon,
  CodeIcon,
  File01Icon,
  ArrowRight01Icon,
} from 'hugeicons-react';
import { taskTemplates, TaskTemplate } from '@/lib/taskTemplates';
import { saveTaskHistory, TaskHistoryItem } from '@/lib/taskHistory';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface Intent {
  goal: string;
  inputs: Record<string, any>;
  constraints?: Record<string, any>;
  budget?: { max_usd?: number };
  sla?: { deadline_ms?: number };
}

interface Proposal {
  _agent: string;
  _agent_name: string;
  _score: number;
  est_cost_usd: number;
  est_latency_ms: number;
  confidence: number;
  plan: string[];
}

type InputType = 'text' | 'file' | 'url' | 'json';

export default function Home() {
  const [intent, setIntent] = useState<Intent>({
    goal: 'extract_event',
    inputs: {
      text: 'Global Scoop AI Hackathon\n\nNov 22–23, 2025 8:30 AM – 5:30 PM\n\nSanta Clara',
    },
    budget: { max_usd: 0.1 },
    sla: { deadline_ms: 5000 },
  });

  const [selectedTemplate, setSelectedTemplate] = useState<string | null>('extract_event');
  const [inputType, setInputType] = useState<InputType>('text');
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [streamingProposals, setStreamingProposals] = useState<Proposal[]>([]);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [showWhy, setShowWhy] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingType, setLoadingType] = useState<'intent' | 'execute' | null>(null);
  const [urlInput, setUrlInput] = useState('');
  const [jsonInput, setJsonInput] = useState('{}');
  const [useOrchestrator, setUseOrchestrator] = useState(false);

  // Add state for new agent registration
  const [newAgent, setNewAgent] = useState({ name: '', url: '' });
  const [isRegistering, setIsRegistering] = useState(false);
  const [availableAgents, setAvailableAgents] = useState<any[]>([]);

  const hubUrl = process.env.NEXT_PUBLIC_HUB_URL || 'http://localhost:8000';

  // Fetch agents on mount
  useEffect(() => {
    const ac = new AbortController();
    const load = async () => {
      try {
        const res = await fetch(`${hubUrl}/agents`, { signal: ac.signal });
        if (!res.ok) return;
        const data = await res.json();
        setAvailableAgents(data);
      } catch (err) {
        // swallow during prerender/hydration
      }
    };
    load();
    return () => ac.abort();
  }, [hubUrl]);

  const handleTemplateSelect = (template: TaskTemplate) => {
    setSelectedTemplate(template.id);
    setIntent({
      goal: template.goal,
      inputs: { ...template.sampleInputs },
      budget: { max_usd: template.defaultBudget },
      sla: { deadline_ms: template.defaultSLA },
    });
  };

  const handleLoadTask = (item: TaskHistoryItem) => {
    setIntent({
      goal: item.goal,
      inputs: item.inputs,
      budget: item.budget,
      sla: item.sla,
    });
    const template = taskTemplates.find((t) => t.goal === item.goal);
    if (template) {
      setSelectedTemplate(template.id);
    }
  };

  const handlePostIntentWithStreaming = async () => {
    setLoading(true);
    setLoadingType('intent');
    setError(null);
    setExecutionResult(null);
    setProposals([]);
    setStreamingProposals([]);

    saveTaskHistory({
      goal: intent.goal,
      inputs: intent.inputs,
      budget: intent.budget,
      sla: intent.sla,
    });

    try {
      const endpoint = useOrchestrator ? `${hubUrl}/orchestrate` : `${hubUrl}/post_intent`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(intent),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const allProposals = data.proposals || [];

      await new Promise((resolve) => setTimeout(resolve, 3000));

      if (allProposals.length > 0) {
        for (let i = 0; i < allProposals.length; i++) {
          await new Promise((resolve) => setTimeout(resolve, 200));
          setStreamingProposals((prev) => [...prev, allProposals[i]]);
        }
        setProposals(allProposals);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to post intent');
      setProposals([]);
      setStreamingProposals([]);
    } finally {
      setLoading(false);
      setLoadingType(null);
    }
  };

  const handlePostIntent = handlePostIntentWithStreaming;

  const handleExecute = async () => {
    setLoading(true);
    setLoadingType('execute');
    setError(null);

    saveTaskHistory({
      goal: intent.goal,
      inputs: intent.inputs,
      budget: intent.budget,
      sla: intent.sla,
    });

    try {
      const response = await fetch(`${hubUrl}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(intent),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setExecutionResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to execute');
      setExecutionResult(null);
    } finally {
      setLoading(false);
      setLoadingType(null);
    }
  };

  const handleRegisterAgent = async () => {
    if (!newAgent.name || !newAgent.url) {
      setError("Name and URL are required");
      return;
    }
    
    setIsRegistering(true);
    setError(null);

    try {
      const response = await fetch(`${hubUrl}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAgent)
      });

      if (!response.ok) throw new Error("Failed to register agent");
      
      // Clear form on success
      setNewAgent({ name: '', url: '' });
      alert("Agent registered successfully! It will now be included in searches.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsRegistering(false);
    }
  };

  const handleFileSelect = (file: File | null) => {
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        setIntent({ ...intent, inputs: { ...intent.inputs, text } });
      };
      reader.readAsText(file);
    }
  };

  const handleUrlFetch = async () => {
    if (!urlInput) return;
    try {
      const response = await fetch(urlInput);
      const text = await response.text();
      setIntent({ ...intent, inputs: { ...intent.inputs, text, url: urlInput } });
    } catch (err) {
      setError(`Failed to fetch URL: ${err}`);
    }
  };

  const handleJsonInput = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      setIntent({ ...intent, inputs: { ...intent.inputs, ...parsed } });
    } catch (err) {
      setError('Invalid JSON input');
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'OK':
        return 'success';
      case 'PARTIAL':
        return 'warning';
      case 'ERROR':
        return 'destructive';
      default:
        return 'default';
    }
  };

  const displayProposals = streamingProposals.length > 0 ? streamingProposals : proposals;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <PageShell>
        <section className="mb-16 pt-12 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <Badge variant="secondary" className="mb-4 px-3 py-1 rounded-full border-white/5 bg-white/5">
              <SparklesIcon className="mr-1 h-3 w-3" />
              <span>Agent Marketplace v1.0</span>
            </Badge>
            <h1 className="font-serif text-5xl md:text-7xl font-medium tracking-tight mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/70">
              Orchestrate Your <br /> Digital Workforce
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8 font-light">
              AgentBridge connects you with specialized autonomous agents. <br className="hidden md:block" />
              Select the best performer for your specific task.
            </p>
          </motion.div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-7 space-y-8">
            <section>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <h2 className="text-xl font-medium mb-4 font-serif">0. Register Agent (Optional)</h2>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Agent Marketplace</CardTitle>
                    <CardDescription>
                      {availableAgents.length} active agents ready for tasks. Register a new one below.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="max-h-32 overflow-y-auto space-y-2 border rounded-md p-2 bg-muted/20">
                      {availableAgents.map((agent: any) => (
                        <div key={agent.id} className="flex justify-between items-center text-sm">
                          <span className="font-medium truncate max-w-[150px]" title={agent.name}>{agent.name}</span>
                          <div className="flex items-center gap-2">
                            {agent.url === 'stdio' && (
                              <Badge variant="secondary" className="text-[10px]">MCP</Badge>
                            )}
                            <Badge variant="outline" className="text-[10px]">{agent.id}</Badge>
                          </div>
                        </div>
                      ))}
                      {availableAgents.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-2">Loading agents...</p>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Agent Name</Label>
                        <Input 
                          placeholder="My Super Agent" 
                          value={newAgent.name}
                          onChange={e => setNewAgent({...newAgent, name: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Agent URL</Label>
                        <Input 
                          placeholder="http://localhost:8000" 
                          value={newAgent.url}
                          onChange={e => setNewAgent({...newAgent, url: e.target.value})}
                        />
                      </div>
                    </div>
                    <Button 
                      onClick={handleRegisterAgent} 
                      disabled={isRegistering}
                      variant="outline" 
                      className="w-full"
                    >
                      {isRegistering ? 'Registering...' : 'Register Agent'}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            </section>

            <section>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <h2 className="text-xl font-medium mb-4 font-serif">1. Choose a Task</h2>
                <TaskTemplateSelector selectedTemplateId={selectedTemplate} onSelectTemplate={handleTemplateSelect} />
              </motion.div>
            </section>

            <section>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                <h2 className="text-xl font-medium mb-4 font-serif">2. Configure Intent</h2>
                <Card>
                  <CardContent className="p-0">
                    <div className="p-6 space-y-6">
                      <div className="space-y-2">
                        <Label htmlFor="goal" className="text-xs uppercase tracking-wider text-muted-foreground">
                          Task Description
                        </Label>
                        <Input
                          id="goal"
                          value={intent.goal}
                          onChange={(e) => setIntent({ ...intent, goal: e.target.value })}
                          placeholder="Describe your task (e.g., Extract dates from this invoice...)"
                          className="font-mono bg-muted/30 border-none"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label className="text-xs uppercase tracking-wider text-muted-foreground">Input Data</Label>
                        <Tabs value={inputType} onValueChange={(v) => setInputType(v as InputType)} className="w-full">
                          <TabsList className="w-full justify-start bg-transparent p-0 h-auto border-b border-white/5 rounded-none mb-4">
                            <TabsTrigger
                              value="text"
                              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                            >
                              <File01Icon className="h-4 w-4 mr-2" /> Text
                            </TabsTrigger>
                            <TabsTrigger
                              value="file"
                              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                            >
                              <File01Icon className="h-4 w-4 mr-2" /> File
                            </TabsTrigger>
                            <TabsTrigger
                              value="url"
                              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                            >
                              <Globe02Icon className="h-4 w-4 mr-2" /> URL
                            </TabsTrigger>
                            <TabsTrigger
                              value="json"
                              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                            >
                              <CodeIcon className="h-4 w-4 mr-2" /> JSON
                            </TabsTrigger>
                          </TabsList>

                          <TabsContent value="text">
                            <Textarea
                              value={intent.inputs.text || ''}
                              onChange={(e) =>
                                setIntent({
                                  ...intent,
                                  inputs: { ...intent.inputs, text: e.target.value },
                                })
                              }
                              rows={5}
                              className="font-mono bg-muted/30 border-none resize-none"
                              placeholder="Enter text to process..."
                            />
                          </TabsContent>

                          <TabsContent value="file">
                            <FileUpload onFileSelect={handleFileSelect} accept=".txt,.pdf,.json,.png,.jpg,.jpeg" maxSize={10} />
                          </TabsContent>

                          <TabsContent value="url" className="flex gap-2">
                            <Input
                              value={urlInput}
                              onChange={(e) => setUrlInput(e.target.value)}
                              placeholder="https://example.com/page"
                              className="bg-muted/30 border-none"
                            />
                            <Button onClick={handleUrlFetch} variant="outline">
                              Fetch
                            </Button>
                          </TabsContent>

                          <TabsContent value="json" className="space-y-2">
                            <Textarea
                              value={jsonInput}
                              onChange={(e) => setJsonInput(e.target.value)}
                              rows={5}
                              className="font-mono bg-muted/30 border-none"
                              placeholder='{"key": "value"}'
                            />
                            <Button onClick={handleJsonInput} variant="outline" size="sm">
                              Apply
                            </Button>
                          </TabsContent>
                        </Tabs>
                      </div>

                      <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="budget" className="text-xs uppercase tracking-wider text-muted-foreground">
                            Budget (USD)
                          </Label>
                          <Input
                            id="budget"
                            type="number"
                            step="0.001"
                            value={intent.budget?.max_usd || 0.1}
                            onChange={(e) =>
                              setIntent({
                                ...intent,
                                budget: { max_usd: parseFloat(e.target.value) || 0.1 },
                              })
                            }
                            className="bg-muted/30 border-none"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="sla" className="text-xs uppercase tracking-wider text-muted-foreground">
                            Deadline (ms)
                          </Label>
                          <Input
                            id="sla"
                            type="number"
                            value={intent.sla?.deadline_ms || 5000}
                            onChange={(e) =>
                              setIntent({
                                ...intent,
                                sla: { deadline_ms: parseInt(e.target.value) || 5000 },
                              })
                            }
                            className="bg-muted/30 border-none"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs uppercase tracking-wider text-muted-foreground">Use Orchestrator</Label>
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={useOrchestrator}
                              onChange={(e) => setUseOrchestrator(e.target.checked)}
                            />
                            <span className="text-xs text-muted-foreground">Route intent to orchestrator</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="p-6 border-t border-white/5 flex gap-3 bg-muted/10">
                      <Button onClick={handlePostIntent} disabled={loading} className="w-full" size="lg">
                        {loading && loadingType === 'intent' ? (
                          <>
                            <Loading03Icon className="mr-2 h-4 w-4 animate-spin" />
                            Negotiating...
                          </>
                        ) : (
                          <>
                            Find Agents
                            <ArrowRight01Icon className="ml-2 h-4 w-4" />
                          </>
                        )}
                      </Button>
                      <Button onClick={handleExecute} disabled={loading} variant="secondary" size="lg">
                        {loading && loadingType === 'execute' ? (
                          <Loading03Icon className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          'Execute'
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-4"
                    >
                      <Alert variant="destructive">
                        <AlertCircleIcon className="h-4 w-4" />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </section>
          </div>

          <div className="lg:col-span-5 space-y-8">
            <section>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                <h2 className="text-xl font-medium mb-4 font-serif">Live Activity</h2>

                {loading && loadingType === 'intent' && displayProposals.length === 0 && (
                  <Card className="mb-6 border-dashed">
                    <CardContent className="pt-6 text-center text-muted-foreground">
                      <div className="h-48 flex items-center justify-center">
                        <div className="space-y-2">
                          <Loading03Icon className="h-8 w-8 animate-spin mx-auto opacity-50" />
                          <p>Negotiating with agent network...</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {displayProposals.length > 0 && (
                  <LiveProposalStream proposals={displayProposals} isLoading={loading && loadingType === 'intent'} />
                )}

                <AnimatePresence>
                  {executionResult && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="mt-6">
                      <Card className="border-green-500/20 bg-green-500/5">
                        <CardHeader>
                          <CardTitle className="flex items-center text-green-500">
                            <CheckmarkCircle02Icon className="mr-2 h-5 w-5" />
                            Task Completed
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div className="flex justify-between items-center p-3 bg-background/40 rounded-lg">
                            <span className="text-sm text-muted-foreground">Winner</span>
                            <Badge variant="success">{executionResult.winner_name}</Badge>
                          </div>
                          <div className="flex justify-between items-center p-3 bg-background/40 rounded-lg">
                            <span className="text-sm text-muted-foreground">Why this agent?</span>
                            <Button variant="outline" size="sm" onClick={() => setShowWhy((v) => !v)}>
                              {showWhy ? 'Hide' : 'Explain'}
                            </Button>
                          </div>
                          {showWhy && executionResult.explanation && (
                            <div className="rounded-lg border bg-background/50 p-4">
                              <div className="text-sm space-y-2">
                                {(() => {
                                  const winner = displayProposals[0];
                                  const peer = displayProposals.length > 1 ? displayProposals[1] : null;
                                  const scoreDelta = peer ? (winner._score - peer._score) : null;
                                  const costDelta = peer ? (winner.est_cost_usd - peer.est_cost_usd) : null;
                                  const latDelta = peer ? (winner.est_latency_ms - peer.est_latency_ms) : null;
                                  const budgetMax = executionResult.explanation.constraints?.budget_max_usd ?? null;
                                  const deadlineMs = executionResult.explanation.constraints?.sla_deadline_ms ?? null;
                                  const cost = executionResult.explanation.inputs?.cost_usd ?? winner?.est_cost_usd;
                                  const latency = executionResult.explanation.inputs?.latency_ms ?? winner?.est_latency_ms;
                                  const budgetHeadroom = budgetMax != null && cost != null ? (budgetMax - cost) : null;
                                  const timeHeadroom = deadlineMs != null && latency != null ? (deadlineMs - latency) : null;
                                  return (
                                    <>
                                      {peer && (
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
                                {Array.isArray(executionResult.proposal?.plan) && (
                                  <div className="mt-2">
                                    <div className="text-xs text-muted-foreground">Plan preview</div>
                                    <ul className="list-disc list-inside text-xs">
                                      {executionResult.proposal.plan.slice(0, 2).map((s: string, i: number) => (
                                        <li key={i} className="font-mono">{s}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {Array.isArray(executionResult.explanation.notes) && (
                                  <ul className="mt-2 list-disc list-inside text-xs text-muted-foreground">
                                    {executionResult.explanation.notes.map((n: string, i: number) => (
                                      <li key={i}>{n}</li>
                                    ))}
                                  </ul>
                                )}
                                <div className="mt-2 text-xs text-muted-foreground">Formula: {executionResult.explanation.formula}</div>
                              </div>
                            </div>
                          )}
                          {executionResult.sandboxId && (
                            <div className="flex justify-between items-center p-3 bg-background/40 rounded-lg">
                              <span className="text-sm text-muted-foreground">Sandbox</span>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">{executionResult.sandboxId}</Badge>
                                {executionResult.logs_url && (
                                  <a href={executionResult.logs_url} target="_blank" rel="noreferrer" className="text-xs underline">View Logs</a>
                                )}
                              </div>
                            </div>
                          )}
                          {executionResult.result?.data && (
                            <div className="rounded-lg border bg-background/50 p-4 overflow-hidden">
                              <pre className="text-xs font-mono overflow-auto max-h-60">
                                {JSON.stringify(executionResult.result.data, null, 2)}
                              </pre>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </section>

            <section>
              <h2 className="text-xl font-medium mb-4 font-serif opacity-50">Recent History</h2>
              <div className="opacity-60 hover:opacity-100 transition-opacity">
                <TaskHistory onLoadTask={handleLoadTask} />
              </div>
            </section>
          </div>
        </div>
      </PageShell>
    </div>
  );
}
