'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  Filter, 
  Mail, 
  Calendar, 
  Award, 
  CheckCircle2, 
  Circle, 
  Loader2, 
  XCircle 
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * AgentStatusCard Component
 * 
 * Displays the status of an individual agent in the workflow.
 * Shows different states: pending, running, completed, failed.
 * Includes animations for running state.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.3)
 * - Animation patterns: https://www.framer.com/motion/
 */

type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';

interface AgentStatusCardProps {
  agent: {
    name: string;
    status: AgentStatus;
    startTime?: number;
    endTime?: number;
    result?: {
      summary?: string;
      count?: number;
    };
  };
}

// Agent icon mapping
const agentIcons = {
  'Sourcing Agent': Search,
  'Screening Agent': Filter,
  'Outreach Agent': Mail,
  'Scheduling Agent': Calendar,
  'Evaluation Agent': Award,
};

// Status icon mapping
const statusIcons = {
  pending: Circle,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};

// Status color mapping
const statusColors = {
  pending: 'text-muted-foreground',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-destructive',
};

// Status background mapping
const statusBackgrounds = {
  pending: 'bg-muted',
  running: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
  completed: 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800',
  failed: 'bg-destructive/10 border-destructive',
};

export default function AgentStatusCard({ agent }: AgentStatusCardProps) {
  const AgentIcon = agentIcons[agent.name as keyof typeof agentIcons] || Search;
  const StatusIcon = statusIcons[agent.status];
  
  // Calculate duration if completed
  const duration = agent.startTime && agent.endTime 
    ? ((agent.endTime - agent.startTime) / 1000).toFixed(1) 
    : null;

  return (
    <Card className={cn(
      'transition-all duration-300',
      statusBackgrounds[agent.status]
    )}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {/* Agent Info */}
          <div className="flex items-start gap-3 flex-1">
            {/* Agent Icon */}
            <div className={cn(
              'p-2 rounded-lg',
              agent.status === 'pending' && 'bg-muted',
              agent.status === 'running' && 'bg-blue-100 dark:bg-blue-900',
              agent.status === 'completed' && 'bg-green-100 dark:bg-green-900',
              agent.status === 'failed' && 'bg-destructive/20'
            )}>
              <AgentIcon className={cn(
                'h-5 w-5',
                statusColors[agent.status]
              )} />
            </div>

            {/* Agent Details */}
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-sm mb-1">{agent.name}</h4>
              
              {/* Status Badge */}
              <Badge 
                variant={agent.status === 'completed' ? 'default' : 'secondary'}
                className={cn(
                  'text-xs',
                  agent.status === 'running' && 'bg-blue-500 text-white',
                  agent.status === 'failed' && 'bg-destructive text-destructive-foreground'
                )}
              >
                {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
              </Badge>

              {/* Result Summary */}
              {agent.result?.summary && (
                <p className="text-xs text-muted-foreground mt-2">
                  {agent.result.summary}
                </p>
              )}

              {/* Duration */}
              {duration && (
                <p className="text-xs text-muted-foreground mt-1">
                  Completed in {duration}s
                </p>
              )}
            </div>
          </div>

          {/* Status Icon */}
          <StatusIcon className={cn(
            'h-5 w-5 flex-shrink-0',
            statusColors[agent.status],
            agent.status === 'running' && 'animate-spin'
          )} />
        </div>

        {/* Result Count (if available) */}
        {agent.result?.count !== undefined && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Results</span>
              <span className="font-semibold">{agent.result.count}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
