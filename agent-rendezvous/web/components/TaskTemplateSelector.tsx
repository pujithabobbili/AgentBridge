import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { taskTemplates, TaskTemplate } from '@/lib/taskTemplates';
import { CheckCircle2 } from 'lucide-react';

interface TaskTemplateSelectorProps {
  selectedTemplateId: string | null;
  onSelectTemplate: (template: TaskTemplate) => void;
}

export function TaskTemplateSelector({ selectedTemplateId, onSelectTemplate }: TaskTemplateSelectorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Task Templates</CardTitle>
        <CardDescription>
          Select a predefined task template or create a custom task
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {taskTemplates.map((template) => (
            <Button
              key={template.id}
              variant={selectedTemplateId === template.id ? "default" : "outline"}
              className="h-auto flex-col items-start p-4 relative"
              onClick={() => onSelectTemplate(template)}
            >
              {selectedTemplateId === template.id && (
                <CheckCircle2 className="absolute top-2 right-2 h-4 w-4" />
              )}
              <div className="text-2xl mb-2">{template.icon}</div>
              <div className="font-semibold text-left mb-1">{template.name}</div>
              <div className="text-xs text-muted-foreground text-left line-clamp-2">
                {template.description}
              </div>
              <div className="flex gap-2 mt-2 text-xs">
                <Badge variant="secondary" className="text-xs">
                  ${template.defaultBudget.toFixed(2)}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {template.defaultSLA}ms
                </Badge>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

