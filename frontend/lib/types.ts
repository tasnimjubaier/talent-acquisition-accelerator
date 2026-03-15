/**
 * TypeScript type definitions for the Talent Acquisition Accelerator frontend
 * Maps to backend data models from shared/models.py
 */

// Job Posting Types
export interface JobPosting {
  jobId?: string;
  jobTitle: string;
  jobDescription: string;
  requiredSkills: string[];
  preferredSkills: string[];
  experienceMin: number;
  experienceMax: number;
  location: string;
  remote: boolean;
  createdAt?: number;
}

// Candidate Types
export interface Candidate {
  candidateId: string;
  name: string;
  email: string;
  phone?: string;
  location: string;
  skills: string[];
  experience: number;
  education: string;
  currentRole?: string;
  matchScore?: number;
  screeningScore?: number;
  screeningPassed?: boolean;
  outreachMessage?: string;
  interviewSlot?: string;
  evaluationScore?: number;
  recommendation?: string;
}

// Workflow Types
export type WorkflowStatus = 'pending' | 'running' | 'completed' | 'failed';
export type AgentName = 'supervisor' | 'sourcing' | 'screening' | 'outreach' | 'scheduling' | 'evaluation';
export type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AgentState {
  agentName: AgentName;
  status: AgentStatus;
  startTime?: number;
  endTime?: number;
  result?: any;
  error?: string;
}

export interface WorkflowState {
  workflowId: string;
  jobId: string;
  status: WorkflowStatus;
  currentAgent: AgentName;
  progress: number;
  agents: AgentState[];
  cost: number;
  estimatedCost: number;
  createdAt: number;
  updatedAt: number;
}

// Activity Feed Types
export interface Activity {
  timestamp: number;
  agentName: AgentName;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

// Results Types
export interface WorkflowResults {
  workflowId: string;
  jobId: string;
  job: JobPosting;
  candidates: Candidate[];
  topCandidates: Candidate[];
  totalCandidates: number;
  qualifiedCandidates: number;
  cost: number;
  duration: number;
  summary: {
    sourced: number;
    screened: number;
    contacted: number;
    scheduled: number;
    recommended: number;
  };
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface StartWorkflowResponse {
  workflowId: string;
  message: string;
}

// Form Types
export interface JobPostingFormData {
  jobTitle: string;
  jobDescription: string;
  requiredSkills: string[];
  preferredSkills: string[];
  experienceMin: number;
  experienceMax: number;
  location: string;
  remote: boolean;
}

// Filter Types
export interface CandidateFilters {
  skills: string[];
  experienceMin: number;
  experienceMax: number;
  location: string;
  minScore: number;
}

// Sort Types
export type SortField = 'name' | 'matchScore' | 'experience' | 'screeningScore';
export type SortOrder = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  order: SortOrder;
}
