'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { taskTemplates, TaskTemplate } from '@/lib/taskTemplates';
import { 
  CheckmarkCircle02Icon, 
  Calendar03Icon, 
  HappyIcon, 
  File01Icon, 
  UserIcon, 
  Invoice01Icon, 
  Tag01Icon, 
  Folder01Icon, 
  Globe02Icon 
} from 'hugeicons-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

interface TaskTemplateSelectorProps {
  selectedTemplateId: string | null;
  onSelectTemplate: (template: TaskTemplate) => void;
}

const iconMap: Record<string, React.ReactNode> = {
  'extract_event': <Calendar03Icon className="h-6 w-6" />,
  'analyze_sentiment': <HappyIcon className="h-6 w-6" />,
  'summarize_text': <File01Icon className="h-6 w-6" />,
  'extract_contact_info': <UserIcon className="h-6 w-6" />,
  'parse_invoice': <Invoice01Icon className="h-6 w-6" />,
  'extract_keywords': <Tag01Icon className="h-6 w-6" />,
  'classify_text': <Folder01Icon className="h-6 w-6" />,
  'translate_text': <Globe02Icon className="h-6 w-6" />,
};

const MotionCard = motion(Card);

export function TaskTemplateSelector({ selectedTemplateId, onSelectTemplate }: TaskTemplateSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {taskTemplates.map((template) => {
        const isSelected = selectedTemplateId === template.id;
        const Icon = iconMap[template.id] || <File01Icon className="h-6 w-6" />;

        return (
          <MotionCard
            key={template.id}
            onClick={() => onSelectTemplate(template)}
            className={cn(
              "relative cursor-pointer transition-all duration-200 hover:shadow-md",
              isSelected 
                ? "bg-primary/5 border-primary/50 ring-1 ring-primary/50" 
                : "hover:bg-accent/50 hover:border-accent-foreground/20"
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <CardHeader className="p-4 pb-2">
              <div className="flex justify-between items-start">
                <div className={cn(
                  "p-2 rounded-lg transition-colors",
                  isSelected ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground group-hover:text-foreground"
                )}>
                  {Icon}
                </div>
                {isSelected && (
                  <div className="text-primary">
                    <CheckmarkCircle02Icon className="h-5 w-5" />
                  </div>
                )}
              </div>
              <CardTitle className={cn(
                "mt-3 text-base font-medium",
                isSelected ? "text-primary" : "text-foreground"
              )}>
                {template.name}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <CardDescription className="line-clamp-2 text-xs mb-4">
                {template.description}
              </CardDescription>
              
              <div className="flex gap-2 mt-auto">
                <Badge variant="secondary" className="text-[10px] px-1.5 h-5">
                  ${template.defaultBudget.toFixed(2)}
                </Badge>
                <Badge variant="outline" className="text-[10px] px-1.5 h-5 border-border/50">
                  {template.defaultSLA}ms
                </Badge>
              </div>
            </CardContent>
          </MotionCard>
        );
      })}
    </div>
  );
}
