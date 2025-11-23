'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Copy, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  variant?: 'default' | 'success' | 'error' | 'warning';
  copyValue?: string;
  className?: string;
}

export function StatCard({
  title,
  value,
  description,
  variant = 'default',
  copyValue,
  className
}: StatCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (copyValue) {
      try {
        await navigator.clipboard.writeText(copyValue);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  const variantStyles = {
    default: 'border-border',
    success: 'border-green-500/50 bg-green-50/50 dark:bg-green-950/20',
    error: 'border-red-500/50 bg-red-50/50 dark:bg-red-950/20',
    warning: 'border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20',
  };

  const iconMap = {
    default: null,
    success: <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />,
    error: <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />,
    warning: <Clock className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />,
  };

  return (
    <Card className={cn(variantStyles[variant], className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {copyValue && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={handleCopy}
            aria-label={`Copy ${title}`}
          >
            {copied ? (
              <CheckCircle2 className="h-3 w-3 text-green-600" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          {iconMap[variant]}
          <div className="text-2xl font-bold">{value}</div>
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

