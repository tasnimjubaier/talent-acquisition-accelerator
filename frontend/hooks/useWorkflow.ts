import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { 
  startWorkflow, 
  getWorkflowStatus, 
  getWorkflowResults 
} from '@/lib/api';
import { useWorkflowStore } from '@/store/workflowStore';
import type { JobPosting, WorkflowState, WorkflowResults } from '@/lib/types';

/**
 * Hook for starting a new workflow
 */
export const useStartWorkflow = () => {
  const router = useRouter();
  const setCurrentWorkflowId = useWorkflowStore((state) => state.setCurrentWorkflowId);
  
  return useMutation({
    mutationFn: (jobPosting: JobPosting) => startWorkflow(jobPosting),
    onSuccess: (data) => {
      setCurrentWorkflowId(data.workflowId);
      router.push(`/workflow/${data.workflowId}`);
    },
    onError: (error) => {
      console.error('Failed to start workflow:', error);
    },
  });
};

/**
 * Hook for fetching workflow status with automatic polling
 */
export const useWorkflowStatus = (workflowId: string | null) => {
  return useQuery({
    queryKey: ['workflow', workflowId, 'status'],
    queryFn: () => {
      if (!workflowId) throw new Error('No workflow ID');
      return getWorkflowStatus(workflowId);
    },
    enabled: !!workflowId,
    refetchInterval: (data) => {
      // Poll every 2 seconds if workflow is running
      // Stop polling if completed or failed
      if (!data) return false;
      return data.status === 'running' ? 2000 : false;
    },
    staleTime: 0, // Always consider data stale for real-time updates
  });
};

/**
 * Hook for fetching workflow results
 */
export const useWorkflowResults = (workflowId: string | null, enabled: boolean = false) => {
  return useQuery({
    queryKey: ['workflow', workflowId, 'results'],
    queryFn: () => {
      if (!workflowId) throw new Error('No workflow ID');
      return getWorkflowResults(workflowId);
    },
    enabled: !!workflowId && enabled,
    staleTime: 5 * 60 * 1000, // Results are stable, cache for 5 minutes
  });
};

/**
 * Hook for managing workflow lifecycle
 */
export const useWorkflowManager = (workflowId: string | null) => {
  const queryClient = useQueryClient();
  const { data: status, isLoading: statusLoading } = useWorkflowStatus(workflowId);
  const { data: results, isLoading: resultsLoading, refetch: fetchResults } = useWorkflowResults(
    workflowId,
    status?.status === 'completed'
  );
  
  const isRunning = status?.status === 'running';
  const isCompleted = status?.status === 'completed';
  const isFailed = status?.status === 'failed';
  
  const invalidateWorkflow = () => {
    if (workflowId) {
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
    }
  };
  
  return {
    status,
    results,
    isLoading: statusLoading || resultsLoading,
    isRunning,
    isCompleted,
    isFailed,
    fetchResults,
    invalidateWorkflow,
  };
};
