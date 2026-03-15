/**
 * API client for Talent Acquisition Accelerator
 * Handles all communication with AWS API Gateway
 * 
 * This is the main API interface used by React components.
 * It delegates to ApiGatewayService for actual AWS integration.
 * 
 * Usage in components:
 * ```tsx
 * import { startWorkflow, getWorkflowStatus } from '@/lib/api';
 * 
 * const response = await startWorkflow(jobData);
 * const status = await getWorkflowStatus(workflowId);
 * ```
 * 
 * Related Files:
 * - api-gateway.ts - AWS Lambda integration layer
 * - types.ts - TypeScript type definitions
 * - mock-api.ts - Mock API for local development
 */

import ApiGatewayService from './api-gateway';
import type {
  JobPosting,
  StartWorkflowResponse,
  WorkflowState,
  WorkflowResults,
  Candidate,
} from './types';

// Determine if we should use mock API (for local development without AWS)
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

/**
 * Start a new recruiting workflow
 * 
 * @param jobPosting Job posting details
 * @returns Workflow ID and status message
 * 
 * @example
 * ```tsx
 * const response = await startWorkflow({
 *   jobTitle: 'Senior Software Engineer',
 *   jobDescription: 'We are looking for...',
 *   requiredSkills: ['React', 'TypeScript', 'Node.js'],
 *   experienceMin: 5,
 *   experienceMax: 10,
 *   location: 'San Francisco, CA',
 *   remote: true,
 * });
 * console.log(response.workflowId); // "wf_abc123"
 * ```
 */
export const startWorkflow = async (
  jobPosting: JobPosting
): Promise<StartWorkflowResponse> => {
  if (USE_MOCK_API) {
    const { MockApiService } = await import('./mock-api');
    return MockApiService.startWorkflow(jobPosting);
  }
  
  return ApiGatewayService.startWorkflow(jobPosting);
};

/**
 * Get workflow status (for polling)
 * 
 * @param workflowId Workflow ID
 * @returns Current workflow state with agent progress
 * 
 * @example
 * ```tsx
 * const status = await getWorkflowStatus('wf_abc123');
 * console.log(status.progress); // 60
 * console.log(status.currentAgent); // "screening"
 * console.log(status.status); // "running"
 * ```
 */
export const getWorkflowStatus = async (
  workflowId: string
): Promise<WorkflowState> => {
  if (USE_MOCK_API) {
    const { MockApiService } = await import('./mock-api');
    return MockApiService.getWorkflowStatus(workflowId);
  }
  
  return ApiGatewayService.getWorkflowStatus(workflowId);
};

/**
 * Get workflow results
 * 
 * @param workflowId Workflow ID
 * @returns Complete workflow results with candidates
 * 
 * @example
 * ```tsx
 * const results = await getWorkflowResults('wf_abc123');
 * console.log(results.candidates.length); // 47
 * console.log(results.topCandidates[0].name); // "Alice Chen"
 * console.log(results.cost); // 4.87
 * ```
 */
export const getWorkflowResults = async (
  workflowId: string
): Promise<WorkflowResults> => {
  if (USE_MOCK_API) {
    const { MockApiService } = await import('./mock-api');
    return MockApiService.getWorkflowResults(workflowId);
  }
  
  return ApiGatewayService.getWorkflowResults(workflowId);
};

/**
 * Get job details
 * 
 * @param jobId Job ID
 * @returns Job posting details
 * 
 * @example
 * ```tsx
 * const job = await getJob('job_xyz789');
 * console.log(job.jobTitle); // "Senior Software Engineer"
 * ```
 */
export const getJob = async (jobId: string): Promise<JobPosting> => {
  if (USE_MOCK_API) {
    const { MockApiService } = await import('./mock-api');
    return MockApiService.getJob(jobId);
  }
  
  return ApiGatewayService.getJob(jobId);
};

/**
 * Get candidate details
 * 
 * @param candidateId Candidate ID
 * @returns Candidate details
 * 
 * @example
 * ```tsx
 * const candidate = await getCandidate('cand_123');
 * console.log(candidate.name); // "Alice Chen"
 * console.log(candidate.matchScore); // 95
 * ```
 */
export const getCandidate = async (candidateId: string): Promise<Candidate> => {
  if (USE_MOCK_API) {
    const { MockApiService } = await import('./mock-api');
    return MockApiService.getCandidate(candidateId);
  }
  
  return ApiGatewayService.getCandidate(candidateId);
};

/**
 * Health check
 * 
 * @returns Health status and timestamp
 * 
 * @example
 * ```tsx
 * const health = await healthCheck();
 * console.log(health.status); // "healthy"
 * ```
 */
export const healthCheck = async (): Promise<{ status: string; timestamp: number }> => {
  if (USE_MOCK_API) {
    const { MockApiService } = await import('./mock-api');
    return MockApiService.healthCheck();
  }
  
  return ApiGatewayService.healthCheck();
};

// Export types for convenience
export type {
  JobPosting,
  StartWorkflowResponse,
  WorkflowState,
  WorkflowResults,
  Candidate,
} from './types';

// Default export for backward compatibility
export default {
  startWorkflow,
  getWorkflowStatus,
  getWorkflowResults,
  getJob,
  getCandidate,
  healthCheck,
};
