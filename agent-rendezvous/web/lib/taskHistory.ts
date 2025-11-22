export interface TaskHistoryItem {
  id: string;
  timestamp: number;
  goal: string;
  inputs: Record<string, any>;
  budget?: { max_usd?: number };
  sla?: { deadline_ms?: number };
  result?: any;
}

const HISTORY_KEY = 'agent_rendezvous_task_history';
const MAX_HISTORY_ITEMS = 50;

export function saveTaskHistory(item: Omit<TaskHistoryItem, 'id' | 'timestamp'>): string {
  if (typeof window === 'undefined') return '';
  
  const history = getTaskHistory();
  const newItem: TaskHistoryItem = {
    ...item,
    id: Date.now().toString(),
    timestamp: Date.now(),
  };
  
  // Add to beginning
  history.unshift(newItem);
  
  // Keep only last MAX_HISTORY_ITEMS
  const trimmed = history.slice(0, MAX_HISTORY_ITEMS);
  
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
  } catch (e) {
    console.error('Failed to save task history:', e);
  }
  
  return newItem.id;
}

export function getTaskHistory(): TaskHistoryItem[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to load task history:', e);
  }
  
  return [];
}

export function deleteTaskHistoryItem(id: string): void {
  if (typeof window === 'undefined') return;
  
  const history = getTaskHistory();
  const filtered = history.filter(item => item.id !== id);
  
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
  } catch (e) {
    console.error('Failed to delete task history item:', e);
  }
}

export function clearTaskHistory(): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch (e) {
    console.error('Failed to clear task history:', e);
  }
}

export function updateTaskHistoryItem(id: string, updates: Partial<TaskHistoryItem>): void {
  if (typeof window === 'undefined') return;
  
  const history = getTaskHistory();
  const index = history.findIndex(item => item.id === id);
  
  if (index !== -1) {
    history[index] = { ...history[index], ...updates };
    
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
      console.error('Failed to update task history item:', e);
    }
  }
}

