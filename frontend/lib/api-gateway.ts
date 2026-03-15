/**
 * API Gateway Integration Layer
 * 
 * Maps frontend API calls to AWS Lambda functions via API Gateway.
 * Handles request/response transformation between frontend and backend.
 * 
 * Architecture:
 * Frontend → API Gateway → Lambda Functions → DynamoDB/Bedrock
 * 
 * Related Governing Docs:
 * - 07_system_architecture.md - Multi-agent architecture
 * - 08_agent_specifications.md - Agent interfaces
 * 
 * Verification Sources:
 * - AWS API Gateway: https://docs.aws.amazon.com/apigateway/
 * - AWS Lambda: https://docs.aws.amazon.com/lambda/
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  JobPosting,
  StartWorkflowResponse,
  WorkflowState,
  WorkflowResults,
  Candidate,
  AgentState,
} from './types';

// API Gateway configuration
const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:3001';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

/**
 * Create configured axios instance for API Gateway
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_GATEWAY_URL,
    timeout: 60000, // 60 seconds for long-running operations
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY && { 'x-api-key': API_KEY }),
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error('[API] Request error:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      console.log(`[API] Response:`, response.status, response.data);
      return response;
    },
    (error: AxiosError) => {
      console.error('[API] Response error:', error.response?.data || error.message);
      
      // Transform error for frontend
      const errorMessage = 
        (error.response?.data as any)?.error || 
        error.message || 
        'An unexpected error occurred';
      
      throw new Error(errorMessage);
    }
  );

  return client;
};

const apiClient = createApiClient();

/**
 * API Gateway Service
 * Provides methods to interact with backend Lambda functions
 */
export class ApiGatewayService {
  /**
   * Start a new recruiting workflow
   * 
   * POST /workflow/start
   * → Supervisor Lambda (start_workflow operation)
   * 
   * @param jobPosting Job posting details
   * @returns Workflow ID and status
   */
  static async startWorkflow(jobPosting: JobPosting): Promise<StartWorkflowResponse> {
    try {
      // First, create the job in DynamoDB
      const jobResponse = await apiClient.post('/jobs', {
        jobTitle: jobPosting.jobTitle,
        jobDescription: jobPosting.jobDescription,
        requiredSkills: jobPosting.requiredSkills,
        preferredSkills: jobPosting.preferredSkills || [],
        experienceMin: jobPosting.experienceMin,
        experienceMax: jobPosting.experienceMax,
        location: jobPosting.location,
        remote: jobPosting.remote,
      });

      const jobId = jobResponse.data.jobId;

      // Start the workflow with the supervisor agent
      const workflowResponse = await apiClient.post('/workflow/start', {
        operation: 'start_workflow',
        job_id: jobId,
        workflow_config: {
          max_candidates: 100,
          screening_threshold: 70,
          enable_outreach: true,
          enable_scheduling: true,
        },
      });

      return {
        workflowId: workflowResponse.data.state_id,
        message: 'Workflow started successfully',
      };
    } catch (error) {
      console.error('Error starting workflow:', error);
      throw error;
    }
  }

  /**
   * Get workflow status (for polling)
   * 
   * GET /workflow/:workflowId/status
   * → Supervisor Lambda (get_status operation)
   * 
   * @param workflowId Workflow ID
   * @returns Current workflow state
   */
  static async getWorkflowStatus(workflowId: string): Promise<WorkflowState> {
    try {
      const response = await apiClient.get(`/workflow/${workflowId}/status`);
      
      const data = response.data;
      
      // Transform backend response to frontend format
      return {
        workflowId: data.state_id,
        jobId: data.job_id,
        status: this.mapWorkflowStatus(data.status),
        currentAgent: data.current_agent || 'supervisor',
        progress: this.calculateProgress(data.agents_completed, data.total_agents),
        agents: this.mapAgentStates(data.agent_states || []),
        cost: data.total_cost || 0,
        estimatedCost: data.estimated_cost || 5.0,
        createdAt: data.created_at || Date.now(),
        updatedAt: data.updated_at || Date.now(),
      };
    } catch (error) {
      console.error('Error getting workflow status:', error);
      throw error;
    }
  }

  /**
   * Get workflow results
   * 
   * GET /workflow/:workflowId/results
   * → Aggregates data from DynamoDB
   * 
   * @param workflowId Workflow ID
   * @returns Complete workflow results
   */
  static async getWorkflowResults(workflowId: string): Promise<WorkflowResults> {
    try {
      const response = await apiClient.get(`/workflow/${workflowId}/results`);
      
      const data = response.data;
      
      // Transform backend response to frontend format
      return {
        workflowId: data.workflow_id,
        jobId: data.job_id,
        job: data.job,
        candidates: data.candidates || [],
        topCandidates: data.top_candidates || [],
        totalCandidates: data.total_candidates || 0,
        qualifiedCandidates: data.qualified_candidates || 0,
        cost: data.total_cost || 0,
        duration: data.duration || 0,
        summary: {
          sourced: data.summary?.sourced || 0,
          screened: data.summary?.screened || 0,
          contacted: data.summary?.contacted || 0,
          scheduled: data.summary?.scheduled || 0,
          recommended: data.summary?.recommended || 0,
        },
      };
    } catch (error) {
      console.error('Error getting workflow results:', error);
      throw error;
    }
  }

  /**
   * Get job details
   * 
   * GET /jobs/:jobId
   * → DynamoDB query
   * 
   * @param jobId Job ID
   * @returns Job posting details
   */
  static async getJob(jobId: string): Promise<JobPosting> {
    try {
      const response = await apiClient.get(`/jobs/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting job:', error);
      throw error;
    }
  }

  /**
   * Get candidate details
   * 
   * GET /candidates/:candidateId
   * → DynamoDB query
   * 
   * @param candidateId Candidate ID
   * @returns Candidate details
   */
  static async getCandidate(candidateId: string): Promise<Candidate> {
    try {
      const response = await apiClient.get(`/candidates/${candidateId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting candidate:', error);
      throw error;
    }
  }

  /**
   * Health check
   * 
   * GET /health
   * 
   * @returns Health status
   */
  static async healthCheck(): Promise<{ status: string; timestamp: number }> {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }

  // Helper methods

  /**
   * Map backend workflow status to frontend status
   */
  private static mapWorkflowStatus(backendStatus: string): 'pending' | 'running' | 'completed' | 'failed' {
    const statusMap: Record<string, 'pending' | 'running' | 'completed' | 'failed'> = {
      'initialized': 'pending',
      'in_progress': 'running',
      'running': 'running',
      'completed': 'completed',
      'failed': 'failed',
      'error': 'failed',
    };
    
    return statusMap[backendStatus] || 'pending';
  }

  /**
   * Calculate progress percentage
   */
  private static calculateProgress(completed: number, total: number): number {
    if (!total || total === 0) return 0;
    return Math.round((completed / total) * 100);
  }

  /**
   * Map backend agent states to frontend format
   */
  private static mapAgentStates(backendStates: any[]): AgentState[] {
    const agentOrder = ['sourcing', 'screening', 'outreach', 'scheduling', 'evaluation'];
    
    return agentOrder.map((agentName) => {
      const backendState = backendStates.find((s) => s.agent_name === agentName);
      
      if (!backendState) {
        return {
          agentName: agentName as any,
          status: 'pending',
        };
      }
      
      return {
        agentName: backendState.agent_name,
        status: this.mapAgentStatus(backendState.status),
        startTime: backendState.start_time,
        endTime: backendState.end_time,
        result: backendState.result,
        error: backendState.error,
      };
    });
  }

  /**
   * Map backend agent status to frontend status
   */
  private static mapAgentStatus(backendStatus: string): 'pending' | 'running' | 'completed' | 'failed' {
    const statusMap: Record<string, 'pending' | 'running' | 'completed' | 'failed'> = {
      'pending': 'pending',
      'running': 'running',
      'in_progress': 'running',
      'completed': 'completed',
      'success': 'completed',
      'failed': 'failed',
      'error': 'failed',
    };
    
    return statusMap[backendStatus] || 'pending';
  }
}

// Export singleton instance
export default ApiGatewayService;
