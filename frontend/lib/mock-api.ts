/**
 * Mock API Service for Local Development
 * 
 * Simulates AWS Lambda responses without requiring AWS infrastructure.
 * Useful for:
 * - Local development without AWS costs
 * - Frontend testing without backend
 * - Demo scenarios with predictable data
 * 
 * Enable by setting: NEXT_PUBLIC_USE_MOCK_API=true
 * 
 * Related Files:
 * - api.ts - Main API client
 * - api-gateway.ts - Real AWS integration
 */

import type {
  JobPosting,
  StartWorkflowResponse,
  WorkflowState,
  WorkflowResults,
  Candidate,
  AgentState,
} from './types';

// In-memory storage for mock data
const mockWorkflows = new Map<string, any>();
const mockJobs = new Map<string, JobPosting>();
const mockCandidates = new Map<string, Candidate>();

/**
 * Generate mock candidate data
 */
const generateMockCandidates = (count: number, jobSkills: string[]): Candidate[] => {
  const names = [
    'Alice Chen', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Johnson',
    'Frank Brown', 'Grace Lee', 'Henry Taylor', 'Iris Martinez', 'Jack Anderson',
    'Kate Thompson', 'Liam Garcia', 'Maya Rodriguez', 'Noah White', 'Olivia Harris',
  ];

  const locations = [
    'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA', 'Boston, MA',
    'Denver, CO', 'Portland, OR', 'Chicago, IL', 'Los Angeles, CA', 'Miami, FL',
  ];

  const educationLevels = [
    'Bachelor\'s in Computer Science',
    'Master\'s in Software Engineering',
    'Bachelor\'s in Information Technology',
    'PhD in Computer Science',
    'Bachelor\'s in Engineering',
  ];

  const roles = [
    'Senior Software Engineer', 'Full Stack Developer', 'Frontend Engineer',
    'Backend Engineer', 'Tech Lead', 'Software Architect',
  ];

  return Array.from({ length: count }, (_, i) => {
    const matchScore = Math.max(60, Math.min(98, 85 + (Math.random() - 0.5) * 30));
    const experience = Math.floor(Math.random() * 10) + 2;
    
    // Select skills (include some from job requirements)
    const candidateSkills = [
      ...jobSkills.slice(0, Math.floor(Math.random() * jobSkills.length) + 1),
      'Git', 'Agile', 'CI/CD',
    ].slice(0, 5 + Math.floor(Math.random() * 3));

    return {
      candidateId: `cand_${i + 1}`,
      name: names[i % names.length] + (i >= names.length ? ` ${Math.floor(i / names.length) + 1}` : ''),
      email: `candidate${i + 1}@example.com`,
      phone: `+1-555-${String(i).padStart(4, '0')}`,
      location: locations[i % locations.length],
      skills: candidateSkills,
      experience,
      education: educationLevels[i % educationLevels.length],
      currentRole: roles[i % roles.length],
      matchScore: Math.round(matchScore),
      screeningScore: Math.round(matchScore * 0.95),
      screeningPassed: matchScore >= 70,
      outreachMessage: `Hi ${names[i % names.length].split(' ')[0]}, we have an exciting opportunity...`,
      interviewSlot: i < 10 ? `2026-03-${18 + Math.floor(i / 2)}T${9 + (i % 2) * 5}:00:00Z` : undefined,
      evaluationScore: Math.round(matchScore * 0.98),
      recommendation: i < 5 ? 'Highly recommended' : i < 15 ? 'Recommended' : 'Consider',
    };
  }).sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));
};

/**
 * Simulate workflow progression
 */
const simulateWorkflowProgress = (workflowId: string) => {
  const workflow = mockWorkflows.get(workflowId);
  if (!workflow || workflow.status === 'completed' || workflow.status === 'failed') {
    return;
  }

  const agentOrder = ['sourcing', 'screening', 'outreach', 'scheduling', 'evaluation'];
  const currentIndex = agentOrder.indexOf(workflow.currentAgent);

  // Progress current agent
  const currentAgentState = workflow.agents.find((a: AgentState) => a.agentName === workflow.currentAgent);
  if (currentAgentState && currentAgentState.status === 'running') {
    // Simulate completion after some time
    const elapsed = Date.now() - (currentAgentState.startTime || Date.now());
    if (elapsed > 3000) { // 3 seconds
      currentAgentState.status = 'completed';
      currentAgentState.endTime = Date.now();
      
      // Move to next agent
      if (currentIndex < agentOrder.length - 1) {
        workflow.currentAgent = agentOrder[currentIndex + 1];
        const nextAgentState = workflow.agents.find((a: AgentState) => a.agentName === workflow.currentAgent);
        if (nextAgentState) {
          nextAgentState.status = 'running';
          nextAgentState.startTime = Date.now();
        }
      } else {
        // All agents completed
        workflow.status = 'completed';
        workflow.progress = 100;
      }
    }
  }

  // Update progress
  const completedAgents = workflow.agents.filter((a: AgentState) => a.status === 'completed').length;
  workflow.progress = Math.round((completedAgents / agentOrder.length) * 100);
  workflow.updatedAt = Date.now();

  mockWorkflows.set(workflowId, workflow);
};

/**
 * Mock API Service
 */
export class MockApiService {
  /**
   * Start a new recruiting workflow
   */
  static async startWorkflow(jobPosting: JobPosting): Promise<StartWorkflowResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    const workflowId = `wf_${Date.now()}`;
    const jobId = `job_${Date.now()}`;

    // Store job
    mockJobs.set(jobId, { ...jobPosting, jobId });

    // Create workflow state
    const agentOrder = ['sourcing', 'screening', 'outreach', 'scheduling', 'evaluation'];
    const agents: AgentState[] = agentOrder.map((name, index) => ({
      agentName: name as any,
      status: index === 0 ? 'running' : 'pending',
      startTime: index === 0 ? Date.now() : undefined,
    }));

    const workflow = {
      workflowId,
      jobId,
      status: 'running',
      currentAgent: 'sourcing',
      progress: 0,
      agents,
      cost: 0,
      estimatedCost: 5.0,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    mockWorkflows.set(workflowId, workflow);

    // Generate mock candidates
    const candidates = generateMockCandidates(47, jobPosting.requiredSkills);
    candidates.forEach(c => mockCandidates.set(c.candidateId, c));

    // Store candidates with workflow
    workflow.candidates = candidates;

    return {
      workflowId,
      message: 'Workflow started successfully (mock)',
    };
  }

  /**
   * Get workflow status
   */
  static async getWorkflowStatus(workflowId: string): Promise<WorkflowState> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));

    // Simulate progress
    simulateWorkflowProgress(workflowId);

    const workflow = mockWorkflows.get(workflowId);
    if (!workflow) {
      throw new Error('Workflow not found');
    }

    // Simulate cost increase
    const completedAgents = workflow.agents.filter((a: AgentState) => a.status === 'completed').length;
    workflow.cost = Math.min(4.87, completedAgents * 0.97);

    return {
      workflowId: workflow.workflowId,
      jobId: workflow.jobId,
      status: workflow.status,
      currentAgent: workflow.currentAgent,
      progress: workflow.progress,
      agents: workflow.agents,
      cost: workflow.cost,
      estimatedCost: workflow.estimatedCost,
      createdAt: workflow.createdAt,
      updatedAt: workflow.updatedAt,
    };
  }

  /**
   * Get workflow results
   */
  static async getWorkflowResults(workflowId: string): Promise<WorkflowResults> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    const workflow = mockWorkflows.get(workflowId);
    if (!workflow) {
      throw new Error('Workflow not found');
    }

    const job = mockJobs.get(workflow.jobId);
    if (!job) {
      throw new Error('Job not found');
    }

    const candidates = workflow.candidates || [];
    const topCandidates = candidates.slice(0, 3);
    const qualifiedCandidates = candidates.filter((c: Candidate) => (c.matchScore || 0) >= 70);

    return {
      workflowId: workflow.workflowId,
      jobId: workflow.jobId,
      job,
      candidates,
      topCandidates,
      totalCandidates: candidates.length,
      qualifiedCandidates: qualifiedCandidates.length,
      cost: workflow.cost,
      duration: Date.now() - workflow.createdAt,
      summary: {
        sourced: candidates.length,
        screened: qualifiedCandidates.length,
        contacted: Math.min(15, qualifiedCandidates.length),
        scheduled: Math.min(10, qualifiedCandidates.length),
        recommended: Math.min(5, qualifiedCandidates.length),
      },
    };
  }

  /**
   * Get job details
   */
  static async getJob(jobId: string): Promise<JobPosting> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 100));

    const job = mockJobs.get(jobId);
    if (!job) {
      throw new Error('Job not found');
    }

    return job;
  }

  /**
   * Get candidate details
   */
  static async getCandidate(candidateId: string): Promise<Candidate> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 100));

    const candidate = mockCandidates.get(candidateId);
    if (!candidate) {
      throw new Error('Candidate not found');
    }

    return candidate;
  }

  /**
   * Health check
   */
  static async healthCheck(): Promise<{ status: string; timestamp: number }> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 50));

    return {
      status: 'healthy (mock)',
      timestamp: Date.now(),
    };
  }
}

export default MockApiService;
