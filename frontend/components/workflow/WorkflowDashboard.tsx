'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import AgentStatusCard from './AgentStatusCard';
import ProgressTracker from './ProgressTracker';
import CostTracker from './CostTracker';
import { AlertCircle, ArrowRight } from 'lucide-react';

/**
 * WorkflowDashboard Component
 * 
 * Main dashboard for displaying real-time workflow status.
 * Orchestrates all workflow-related components and handles polling.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.2)
 * - React Query polling: https://tanstack.com/query/latest/docs/react/guides/window-focus-refetching
 */

type WorkflowStatus = 'running' | 'completed' | 'failed';
type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';

interface WorkflowDashboardProps {
  workflowId: string;
  status: WorkflowStatus;
  currentAgent?: string;
  progress: number;
  agents: {
    name: string;
    status: AgentStatus;
    startTime?: number;
    endTime?: number;
    result?: {
      summary?: string;
      count?: number;
    };
  }[];
  cost: number;
  estimatedCost: number;
  costBreakdown?: {
    agent: string;
    cost: number;
  }[];
  error?: string;
  onRefresh?: () => void;
}

// Agent workflow steps
const WORKFLOW_STEPS = [
  'Sourcing',
  'Screening',
  'Outreach',
  'Scheduling',
  'Evaluation'
];

export default function WorkflowDashboard({
  workflowId,
  status,
  currentAgent,
  progress,
  agents,
  cost,
  estimatedCost,
  costBreakdown,
  error,
  onRefresh
}: WorkflowDashboardProps) {
  const router = useRouter();

  // Auto-refresh while running (handled by parent with React Query)
  useEffect(() => {
    if (status === 'running' && onRefresh) {
      const interval = setInterval(onRefresh, 2000);
      return () => clearInterval(interval);
    }
  }, [status, onRefresh]);

  // Calculate current step index
  const getCurrentStepIndex = () => {
    const completedAgents = agents.filter(a => a.status === 'completed').length;
    return Math.min(completedAgents, WORKFLOW_STEPS.length - 1);
  };

  // Handle view results
  const handleViewResults = () => {
    router.push(`/results/${workflowId}`);
  };

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Progress Tracker */}
      <div className="bg-card rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-6">Workflow Progress</h3>
        <ProgressTracker 
          currentStep={getCurrentStepIndex()} 
          steps={WORKFLOW_STEPS}
        />
      </div>

      {/* Agent Status and Cost Tracker Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status Cards */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold">Agent Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <AgentStatusCard key={agent.name} agent={agent} />
            ))}
          </div>
        </div>

        {/* Cost Tracker */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Cost Tracking</h3>
          <CostTracker
            currentCost={cost}
            estimatedCost={estimatedCost}
            breakdown={costBreakdown}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className="bg-muted rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">
              {status === 'running' && `Currently running: ${currentAgent || 'Initializing...'}`}
              {status === 'completed' && '✓ Workflow completed successfully!'}
              {status === 'failed' && '✗ Workflow failed'}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {status === 'running' && 'This may take a few minutes...'}
              {status === 'completed' && 'All agents have finished processing'}
              {status === 'failed' && 'Please check the error message above'}
            </p>
          </div>

          {/* View Results Button */}
          {status === 'completed' && (
            <Button onClick={handleViewResults} size="lg">
              View Results
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Activity Feed (Optional - can be added later) */}
      {status === 'running' && (
        <div className="bg-card rounded-lg border p-4">
          <h3 className="text-sm font-semibold mb-3">Recent Activity</h3>
          <div className="space-y-2 text-sm text-muted-foreground">
            {agents
              .filter(a => a.status === 'completed' || a.status === 'running')
              .map((agent, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="text-primary">●</span>
                  <span>
                    {agent.name}: {agent.result?.summary || 'Processing...'}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
