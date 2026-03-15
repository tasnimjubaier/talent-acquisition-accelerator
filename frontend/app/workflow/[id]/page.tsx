'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useWorkflowManager } from '@/hooks/useWorkflow';
import WorkflowDashboard from '@/components/workflow/WorkflowDashboard';
import JobSummaryCard from '@/components/job/JobSummaryCard';
import { ArrowLeft, AlertCircle } from 'lucide-react';

/**
 * Workflow Status Page
 * 
 * Real-time monitoring of AI agent workflow execution.
 * Shows live progress, agent status, cost tracking, and job details.
 * 
 * Features:
 * - WorkflowDashboard with auto-refresh polling
 * - Job summary display
 * - Real-time agent status updates
 * - Cost tracking
 * - Progress visualization
 * - Automatic navigation to results when complete
 * 
 * Related Governing Docs:
 * - 00_frontend_specification.md - Workflow page requirements
 * - 07_system_architecture.md - Multi-agent workflow
 * - 11_user_experience_design.md - Real-time updates UX
 */
export default function WorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  
  const { status, isLoading, isRunning, isCompleted, isFailed } = useWorkflowManager(workflowId);
  
  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading workflow...</p>
          </div>
        </div>
      </div>
    );
  }
  
  // Not found state
  if (!status) {
    return (
      <div className="container mx-auto p-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" />
              <p className="text-lg font-medium">Workflow not found</p>
              <p className="text-sm text-muted-foreground">
                The workflow ID "{workflowId}" does not exist or has been deleted.
              </p>
              <Button onClick={() => router.push('/')} variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4 md:p-8 space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => router.push('/')}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl md:text-3xl font-bold">Workflow Status</h1>
          <p className="text-sm text-muted-foreground">ID: {workflowId}</p>
        </div>
      </div>

      {/* Job Summary */}
      {status.job && (
        <JobSummaryCard job={status.job} />
      )}

      {/* Workflow Dashboard - Main Component */}
      <WorkflowDashboard workflowId={workflowId} />

      {/* Success Alert - Workflow Completed */}
      {isCompleted && (
        <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
          <AlertDescription className="flex items-center justify-between">
            <span className="text-green-700 dark:text-green-300">
              ✓ Workflow completed successfully! Your results are ready.
            </span>
            <Button 
              onClick={() => router.push(`/results/${workflowId}`)}
              className="ml-4"
            >
              View Results
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Error Alert - Workflow Failed */}
      {isFailed && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-semibold">Workflow Failed</p>
              <p className="text-sm">
                {status.error || 'An error occurred during workflow execution. Please try again or contact support.'}
              </p>
              <div className="flex gap-2 mt-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => router.push('/')}
                >
                  Create New Job
                </Button>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Running Status Info */}
      {isRunning && (
        <Alert>
          <AlertDescription className="text-sm">
            <p className="font-medium mb-1">Workflow in progress</p>
            <p className="text-muted-foreground">
              This page auto-refreshes every 5 seconds. You can safely navigate away and return later.
            </p>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
