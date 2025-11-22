import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Loader2, AlertCircle, CheckCircle2, Trophy } from 'lucide-react';

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

interface Result {
  status: string;
  data: Record<string, any>;
  metrics: Record<string, any>;
  evidence: Record<string, any>;
  error?: string;
}

export default function Home() {
  const [intent, setIntent] = useState<Intent>({
    goal: 'extract_event',
    inputs: {
      text: 'Global Scoop AI Hackathon\n\nNov 22–23, 2025 8:30 AM – 5:30 PM\n\nSanta Clara'
    },
    budget: { max_usd: 0.1 },
    sla: { deadline_ms: 5000 }
  });
  
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingType, setLoadingType] = useState<'intent' | 'execute' | null>(null);

  const hubUrl = process.env.NEXT_PUBLIC_HUB_URL || 'http://localhost:8000';

  const handlePostIntent = async () => {
    setLoading(true);
    setLoadingType('intent');
    setError(null);
    setExecutionResult(null);
    
    try {
      const response = await fetch(`${hubUrl}/post_intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(intent)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setProposals(data.proposals || []);
    } catch (err: any) {
      setError(err.message || 'Failed to post intent');
      setProposals([]);
    } finally {
      setLoading(false);
      setLoadingType(null);
    }
  };

  const handleExecute = async () => {
    setLoading(true);
    setLoadingType('execute');
    setError(null);
    
    try {
      const response = await fetch(`${hubUrl}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(intent)
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

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-2">Agent Rendezvous</h1>
          <p className="text-muted-foreground text-lg">
            Agent-to-agent selection and execution system
          </p>
        </div>

        {/* Intent Configuration Card */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Intent Configuration</CardTitle>
            <CardDescription>
              Configure your task goal, inputs, budget, and SLA requirements
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="goal">Goal</Label>
              <Input
                id="goal"
                value={intent.goal}
                onChange={(e) => setIntent({ ...intent, goal: e.target.value })}
                placeholder="e.g., extract_event"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="inputs">Input Text</Label>
              <Textarea
                id="inputs"
                value={intent.inputs.text}
                onChange={(e) => setIntent({ 
                  ...intent, 
                  inputs: { ...intent.inputs, text: e.target.value }
                })}
                rows={5}
                className="font-mono"
                placeholder="Enter text to process..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="budget">Max Budget (USD)</Label>
                <Input
                  id="budget"
                  type="number"
                  step="0.001"
                  value={intent.budget?.max_usd || 0.1}
                  onChange={(e) => setIntent({ 
                    ...intent, 
                    budget: { max_usd: parseFloat(e.target.value) || 0.1 }
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sla">SLA Deadline (ms)</Label>
                <Input
                  id="sla"
                  type="number"
                  value={intent.sla?.deadline_ms || 5000}
                  onChange={(e) => setIntent({ 
                    ...intent, 
                    sla: { deadline_ms: parseInt(e.target.value) || 5000 }
                  })}
                />
              </div>
            </div>

            <div className="flex gap-4">
              <Button
                onClick={handlePostIntent}
                disabled={loading}
                variant="default"
              >
                {loading && loadingType === 'intent' ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  'Post Intent'
                )}
              </Button>
              <Button
                onClick={handleExecute}
                disabled={loading}
                variant="secondary"
              >
                {loading && loadingType === 'execute' ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  'Execute'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-8">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Proposals Section */}
        {loading && loadingType === 'intent' ? (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Proposals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-32 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        ) : proposals.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Proposals ({proposals.length})</CardTitle>
              <CardDescription>
                Ranked proposals from available agents
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Proposals Table */}
              <div className="rounded-md border mb-6">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Agent</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>Latency</TableHead>
                      <TableHead>Confidence</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {proposals.map((prop, idx) => (
                      <TableRow key={idx} className={idx === 0 ? 'bg-muted/50' : ''}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            {prop._agent_name}
                            {idx === 0 && (
                              <Badge variant="default" className="gap-1">
                                <Trophy className="h-3 w-3" />
                                Best
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">
                            {prop._score.toFixed(2)}
                          </Badge>
                        </TableCell>
                        <TableCell>${prop.est_cost_usd.toFixed(3)}</TableCell>
                        <TableCell>{prop.est_latency_ms}ms</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {(prop.confidence * 100).toFixed(0)}%
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Detailed Proposal Cards */}
              <div className="space-y-4">
                {proposals.map((prop, idx) => (
                  <Card key={idx} className={idx === 0 ? 'border-primary' : ''}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">
                          {prop._agent_name}
                          {idx === 0 && (
                            <Badge variant="default" className="ml-2">
                              <Trophy className="h-3 w-3 mr-1" />
                              Best Proposal
                            </Badge>
                          )}
                        </CardTitle>
                        <Badge variant="secondary">
                          Score: {prop._score.toFixed(2)}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Cost</p>
                          <p className="font-semibold">${prop.est_cost_usd.toFixed(3)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Latency</p>
                          <p className="font-semibold">{prop.est_latency_ms}ms</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Confidence</p>
                          <p className="font-semibold">{(prop.confidence * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-2">Execution Plan:</p>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                          {prop.plan.map((step, i) => (
                            <li key={i}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Execution Results */}
        {loading && loadingType === 'execute' ? (
          <Card>
            <CardHeader>
              <CardTitle>Execution Result</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-64 w-full" />
              </div>
            </CardContent>
          </Card>
        ) : executionResult && (
          <Card>
            <CardHeader>
              <CardTitle>Execution Result</CardTitle>
              <CardDescription>
                Task executed on the best available agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Winner</p>
                <div className="flex items-center gap-2">
                  <Badge variant="success" className="text-base px-3 py-1">
                    <CheckCircle2 className="h-4 w-4 mr-1" />
                    {executionResult.winner_name}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    ({executionResult.winner})
                  </span>
                </div>
              </div>
              
              {executionResult.result && (
                <>
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Status</p>
                    <Badge variant={getStatusBadgeVariant(executionResult.result.status)}>
                      {executionResult.result.status}
                    </Badge>
                  </div>

                  {executionResult.result.data && Object.keys(executionResult.result.data).length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Data</p>
                      <div className="rounded-lg border bg-muted/50 p-4 overflow-auto">
                        <pre className="text-sm font-mono">
                          {JSON.stringify(executionResult.result.data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {executionResult.result.metrics && (
                    <div>
                      <p className="text-sm font-medium mb-2">Metrics</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="rounded-lg border p-4">
                          <p className="text-sm text-muted-foreground mb-1">Latency</p>
                          <p className="text-2xl font-bold">
                            {executionResult.result.metrics.latency_ms}ms
                          </p>
                        </div>
                        <div className="rounded-lg border p-4">
                          <p className="text-sm text-muted-foreground mb-1">Cost</p>
                          <p className="text-2xl font-bold">
                            ${executionResult.result.metrics.cost_usd.toFixed(3)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {executionResult.result.error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>Error</AlertTitle>
                      <AlertDescription>
                        {executionResult.result.error}
                      </AlertDescription>
                    </Alert>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
