'use client';

import { motion } from 'framer-motion';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';

interface ProgressIndicatorProps {
  progress?: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  indeterminate?: boolean;
}

export function ProgressIndicator({ 
  progress = 0, 
  label, 
  showPercentage = false,
  indeterminate = false 
}: ProgressIndicatorProps) {
  return (
    <div className="space-y-2">
      {label && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{label}</span>
          {showPercentage && !indeterminate && (
            <span className="font-medium">{Math.round(progress)}%</span>
          )}
        </div>
      )}
      <div className="relative">
        {indeterminate ? (
          <Card className="p-1">
            <CardContent className="p-0">
              <motion.div
                className="h-2 bg-primary rounded-full"
                initial={{ width: '0%' }}
                animate={{ 
                  width: ['0%', '100%', '0%'],
                  x: ['0%', '100%', '0%']
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut'
                }}
                style={{ maxWidth: '100%' }}
              />
            </CardContent>
          </Card>
        ) : (
          <Progress value={progress} className="h-2" />
        )}
      </div>
    </div>
  );
}

