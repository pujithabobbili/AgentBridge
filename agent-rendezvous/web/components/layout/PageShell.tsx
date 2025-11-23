'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

interface PageShellProps {
  children: React.ReactNode;
  className?: string;
}

export function PageShell({ children, className }: PageShellProps) {
  return (
    <div className={cn(
      "container mx-auto px-4 md:px-6 lg:px-8 py-12 max-w-5xl min-h-[calc(100vh-3.5rem)]",
      className
    )}>
      {children}
    </div>
  );
}
