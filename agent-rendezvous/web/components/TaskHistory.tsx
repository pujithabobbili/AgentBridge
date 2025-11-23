'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { getTaskHistory, deleteTaskHistoryItem, clearTaskHistory, TaskHistoryItem } from '@/lib/taskHistory';
import { Time01Icon, Delete02Icon, Clock01Icon, Cancel01Icon } from 'hugeicons-react';

// Simple date formatter
const formatDistanceToNow = (date: Date, options?: { addSuffix?: boolean }) => {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    const str = `${minutes} minute${minutes > 1 ? 's' : ''}`;
    return options?.addSuffix ? `${str} ago` : str;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const str = `${hours} hour${hours > 1 ? 's' : ''}`;
    return options?.addSuffix ? `${str} ago` : str;
  }
  const days = Math.floor(hours / 24);
  const str = `${days} day${days > 1 ? 's' : ''}`;
  return options?.addSuffix ? `${str} ago` : str;
};

interface TaskHistoryProps {
  onLoadTask: (item: TaskHistoryItem) => void;
}

export function TaskHistory({ onLoadTask }: TaskHistoryProps) {
  const [history, setHistory] = useState<TaskHistoryItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    loadHistory();
    // Refresh history every 5 seconds
    const interval = setInterval(loadHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadHistory = () => {
    setHistory(getTaskHistory());
  };

  const handleLoad = (item: TaskHistoryItem) => {
    onLoadTask(item);
    setIsOpen(false);
  };

  const handleDelete = (id: string) => {
    deleteTaskHistoryItem(id);
    loadHistory();
  };

  const handleClear = () => {
    if (confirm('Are you sure you want to clear all task history?')) {
      clearTaskHistory();
      loadHistory();
    }
  };

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 right-4 z-50 rounded-full h-10 w-10 shadow-lg bg-background border-white/10"
      >
        <Time01Icon className="h-5 w-5" />
      </Button>

      {isOpen && (
        <Card className="fixed bottom-20 right-4 w-96 max-h-[600px] z-50 shadow-2xl border-white/10 bg-background/95 backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 border-b border-white/5">
            <CardTitle className="text-lg font-medium">Task History</CardTitle>
            <div className="flex gap-2">
              {history.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClear}
                  className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                >
                  <Delete02Icon className="h-4 w-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8 p-0 text-muted-foreground"
              >
                <Cancel01Icon className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[500px] p-4">
              {history.length === 0 ? (
                <div className="text-center text-muted-foreground py-8 text-sm">
                  No task history yet
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((item) => (
                    <Card key={item.id} className="p-3 border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="font-medium text-sm mb-1 font-mono">{item.goal}</div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock01Icon className="h-3 w-3" />
                            {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(item.id)}
                          className="h-6 w-6 p-0 opacity-50 hover:opacity-100 hover:text-destructive"
                        >
                          <Delete02Icon className="h-3 w-3" />
                        </Button>
                      </div>
                      <div className="flex gap-2 mb-3">
                        {item.budget?.max_usd && (
                          <Badge variant="secondary" className="text-[10px] h-5 px-1.5 bg-white/5">
                            ${item.budget.max_usd.toFixed(2)}
                          </Badge>
                        )}
                        {item.sla?.deadline_ms && (
                          <Badge variant="outline" className="text-[10px] h-5 px-1.5 border-white/10">
                            {item.sla.deadline_ms}ms
                          </Badge>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleLoad(item)}
                        className="w-full h-7 text-xs bg-transparent border-white/10 hover:bg-white/5"
                      >
                        Load Task
                      </Button>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </>
  );
}
