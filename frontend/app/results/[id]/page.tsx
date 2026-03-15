'use client';

import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useWorkflowResults } from '@/hooks/useWorkflow';
import ResultsVisualization from '@/components/results/ResultsVisualization';
import CandidatePipeline from '@/components/candidates/CandidatePipeline';
import JobSummaryCard from '@/components/job/JobSummaryCard';
import { ArrowLeft, AlertCircle, Download } from 'lucide-react';


/**
 * Results Page
 * 
 * Comprehensive visualization of workflow results after completion.
 * Shows ranked candidates, skill analysis, outreach messages, schedules, and recommendations.
 * 
 * Features:
 * - ResultsVisualization with tabbed interface
 * - CandidatePipeline for detailed candidate management
 * - Job summary display
 * - Export functionality
 * - Navigation back to workflow or home
 * 
 * Components Used:
 * - TopCandidatesRanking - Podium display of top 3
 * - SkillMatchChart - Radar chart visualization
 * - OutreachPreview - Multi-channel messages
 * - InterviewSchedule - Calendar view
 * - FinalRecommendations - AI recommendations
 * - CandidatePipeline - Full candidate list with filters
 * 
 * Related Governing Docs:
 * - 00_frontend_specification.md - Results page requirements
 * - 11_user_experience_design.md - Results visualization UX
 * - 08_agent_specifications.md - Agent output formats
 */
export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  
  const { data: results, isLoading, error } = useWorkflowResults(workflowId, true);

  // Export results as JSON
  const handleExport = () => {
    if (!results) return;
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow-results-${workflowId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading results...</p>
          </div>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error || !results) {
    return (
      <div className="container mx-auto p-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" />
              <p className="text-lg font-medium">Results not found</p>
              <p className="text-sm text-muted-foreground">
                {error || `The results for workflow "${workflowId}" could not be loaded.`}
              </p>
              <div className="flex gap-2 justify-center">
                <Button onClick={() => router.push(`/workflow/${workflowId}`)} variant="outline">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Workflow
                </Button>
                <Button onClick={() => router.push('/')}>
                  Create New Job
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4 md:p-8 space-y-6">
      {/* Header with Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => router.push(`/workflow/${workflowId}`)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Workflow
          </Button>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Workflow Results</h1>
            <p className="text-sm text-muted-foreground">ID: {workflowId}</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleExport}
          >
            <Download className="w-4 h-4 mr-2" />
            Export Results
          </Button>
          <Button 
            size="sm"
            onClick={() => router.push('/')}
          >
            Create New Job
          </Button>
        </div>
      </div>

      {/* Success Alert */}
      <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
        <AlertDescription className="text-green-700 dark:text-green-300">
          ✓ Workflow completed successfully! Found {results.candidates?.length || 0} candidates.
        </AlertDescription>
      </Alert>

      {/* Job Summary */}
      {results.job && (
        <JobSummaryCard job={results.job} />
      )}

      {/* Main Results Visualization */}
      <ResultsVisualization 
        candidates={results.candidates || []}
        outreachMessages={results.outreachMessages || []}
        interviewSchedules={results.interviewSchedules || []}
        recommendations={results.recommendations}
        workflowId={workflowId}
      />

      {/* Detailed Candidate Pipeline */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold mb-2">All Candidates</h2>
          <p className="text-muted-foreground">
            Search, filter, and manage all candidates from this workflow
          </p>
        </div>
        
        <CandidatePipeline 
          candidates={results.candidates || []}
          workflowId={workflowId}
        />
      </div>

      {/* Cost Summary */}
      {results.cost && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Workflow Cost</p>
                <p className="text-2xl font-bold">${results.cost.total.toFixed(4)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Tokens Used</p>
                <p className="text-lg font-semibold">
                  {results.cost.inputTokens?.toLocaleString() || 0} in / {results.cost.outputTokens?.toLocaleString() || 0} out
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Footer Actions */}
      <div className="flex justify-center gap-4 pt-8 pb-4">
        <Button 
          variant="outline"
          onClick={() => router.push(`/workflow/${workflowId}`)}
        >
          View Workflow Details
        </Button>
        <Button onClick={() => router.push('/')}>
          Create Another Job
        </Button>
      </div>
    </div>
  );
}
