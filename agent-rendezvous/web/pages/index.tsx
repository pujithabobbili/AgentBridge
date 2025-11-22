import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { TaskTemplateSelector } from '@/components/TaskTemplateSelector';
import { TaskHistory } from '@/components/TaskHistory';
import { FileUpload } from '@/components/FileUpload';
import { Loader2, AlertCircle, CheckCircle2, Trophy, Sparkles, Globe, Code, FileText } from 'lucide-react';
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

interface Result {
  status: string;
  data: Record<string, any>;
  metrics: Record<string, any>;
  evidence: Record<string, any>;
  error?: string;
}

type InputType = 'text' | 'file' | 'url' | 'json';

export default function Home() {
  const [intent, setIntent] = useState<Intent>({
    goal: 'extract_event',
    inputs: {
      text: 'Global Scoop AI Hackathon\n\nNov 22–23, 2025 8:30 AM – 5:30 PM\n\nSanta Clara'
    },
    budget: { max_usd: 0.1 },
    sla: { deadline_ms: 5000 }
  });
  
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>('extract_event');
  const [inputType, setInputType] = useState<InputType>('text');
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [streamingProposals, setStreamingProposals] = useState<Proposal[]>([]);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingType, setLoadingType] = useState<'intent' | 'execute' | null>(null);
  const [urlInput, setUrlInput] = useState('');
  const [jsonInput, setJsonInput] = useState('{}');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const hubUrl = process.env.NEXT_PUBLIC_HUB_URL || 'http://localhost:8000';

  // Handle template selection
  const handleTemplateSelect = (template: TaskTemplate) => {
    setSelectedTemplate(template.id);
    setIntent({
      goal: template.goal,
      inputs: { ...template.sampleInputs },
      budget: { max_usd: template.defaultBudget },
      sla: { deadline_ms: template.defaultSLA }
    });
  };

  // Handle task history load
  const handleLoadTask = (item: TaskHistoryItem) => {
    setIntent({
      goal: item.goal,
      inputs: item.inputs,
      budget: item.budget,
      sla: item.sla
    });
    // Find matching template
    const template = taskTemplates.find(t => t.goal === item.goal);
    if (template) {
      setSelectedTemplate(template.id);
    }
  };

  // Real-time proposal streaming
  const handlePostIntentWithStreaming = async () => {
    setLoading(true);
    setLoadingType('intent');
    setError(null);
    setExecutionResult(null);
    setProposals([]);
    setStreamingProposals([]);
    
    // Save to history
    saveTaskHistory({
      goal: intent.goal,
      inputs: intent.inputs,
      budget: intent.budget,
      sla: intent.sla
    });
    
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
      const allProposals = data.proposals || [];
      
      // Simulate streaming: add proposals one by one with animation
      if (allProposals.length > 0) {
        for (let i = 0; i < allProposals.length; i++) {
          await new Promise(resolve => setTimeout(resolve, 200)); // Small delay between proposals
          setStreamingProposals(prev => [...prev, allProposals[i]]);
        }
        // Finalize all proposals
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
    
    // Save to history with result
    const historyId = saveTaskHistory({
      goal: intent.goal,
      inputs: intent.inputs,
      budget: intent.budget,
      sla: intent.sla
    });
    
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

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
    if (file) {
      // Read file content (simplified - in real app, handle different file types)
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

  // Display proposals (use streaming if available, otherwise final)
  const displayProposals = streamingProposals.length > 0 ? streamingProposals : proposals;

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        {/* Header with animation */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-2 mb-2">
            <h1 className="text-4xl font-bold tracking-tight">Agent Rendezvous</h1>
            <Sparkles className="h-6 w-6 text-primary animate-pulse" />
          </div>
          <p className="text-muted-foreground text-lg">
            Agent-to-agent selection and execution system with 8 specialized agents
          </p>
        </motion.div>

        {/* Task Template Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <TaskTemplateSelector
            selectedTemplateId={selectedTemplate}
            onSelectTemplate={handleTemplateSelect}
          />
        </motion.div>

        {/* Intent Configuration Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
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

              {/* Input Type Selector */}
              <div className="space-y-2">
                <Label>Input Type</Label>
                <Tabs value={inputType} onValueChange={(v) => setInputType(v as InputType)}>
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="text">
                      <FileText className="h-4 w-4 mr-2" />
                      Text
                    </TabsTrigger>
                    <TabsTrigger value="file">
                      <FileText className="h-4 w-4 mr-2" />
                      File
                    </TabsTrigger>
                    <TabsTrigger value="url">
                      <Globe className="h-4 w-4 mr-2" />
                      URL
                    </TabsTrigger>
                    <TabsTrigger value="json">
                      <Code className="h-4 w-4 mr-2" />
                      JSON
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="text" className="space-y-2">
                    <Label htmlFor="inputs">Input Text</Label>
                    <Textarea
                      id="inputs"
                      value={intent.inputs.text || ''}
                      onChange={(e) => setIntent({ 
                        ...intent, 
                        inputs: { ...intent.inputs, text: e.target.value }
                      })}
                      rows={5}
                      className="font-mono"
                      placeholder="Enter text to process..."
                    />
                  </TabsContent>
                  
                  <TabsContent value="file" className="space-y-2">
                    <FileUpload
                      onFileSelect={handleFileSelect}
                      accept=".txt,.pdf,.json,.png,.jpg,.jpeg"
                      maxSize={10}
                    />
                  </TabsContent>
                  
                  <TabsContent value="url" className="space-y-2">
                    <Label htmlFor="url">URL</Label>
                    <div className="flex gap-2">
                      <Input
                        id="url"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        placeholder="https://example.com/page"
                        type="url"
                      />
                      <Button type="button" onClick={handleUrlFetch} variant="outline">
                        Fetch
                      </Button>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="json" className="space-y-2">
                    <Label htmlFor="json">JSON Input</Label>
                    <Textarea
                      id="json"
                      value={jsonInput}
                      onChange={(e) => setJsonInput(e.target.value)}
                      rows={5}
                      className="font-mono"
                      placeholder='{"key": "value"}'
                    />
                    <Button type="button" onClick={handleJsonInput} variant="outline">
                      Apply JSON
                    </Button>
                  </TabsContent>
                </Tabs>
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
        </motion.div>

        {/* Error Alert */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-8"
            >
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Proposals Section with Real-time Streaming */}
        {loading && loadingType === 'intent' && displayProposals.length === 0 ? (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Proposals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <Skeleton key={i} className="h-32 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        ) : displayProposals.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>
                  Proposals ({displayProposals.length}{loading && loadingType === 'intent' ? ' streaming...' : ''})
                </CardTitle>
                <CardDescription>
                  Ranked proposals from available agents
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Proposals Table */}
                <div className="rounded-md border mb-6 overflow-hidden">
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
                      {displayProposals.map((prop, idx) => (
                        <TableRow 
                          key={prop._agent} 
                          className={idx === 0 ? 'bg-muted/50' : ''}
                        >
                          <TableCell className="font-medium">
                            <motion.div 
                              className="flex items-center gap-2"
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: idx * 0.05 }}
                            >
                              {prop._agent_name}
                              {idx === 0 && (
                                <Badge variant="default" className="gap-1">
                                  <Trophy className="h-3 w-3" />
                                  Best
                                </Badge>
                              )}
                            </motion.div>
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
                  <AnimatePresence>
                    {displayProposals.map((prop, idx) => (
                      <motion.div
                        key={prop._agent}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ delay: idx * 0.1 }}
                      >
                        <Card className={idx === 0 ? 'border-primary' : ''}>
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
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Execution Results */}
        <AnimatePresence>
          {loading && loadingType === 'execute' && (
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
          )}
          {executionResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
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
            </motion.div>
          )}
        </AnimatePresence>

        {/* Task History Component */}
        <TaskHistory onLoadTask={handleLoadTask} />
      </div>
    </div>
  );
}
