/**
 * Constants for the Talent Acquisition Accelerator frontend
 */

// Agent names
export const AGENT_NAMES = {
  SUPERVISOR: 'supervisor',
  SOURCING: 'sourcing',
  SCREENING: 'screening',
  OUTREACH: 'outreach',
  SCHEDULING: 'scheduling',
  EVALUATION: 'evaluation',
} as const;

// Agent display names
export const AGENT_DISPLAY_NAMES = {
  supervisor: 'Supervisor',
  sourcing: 'Sourcing Agent',
  screening: 'Screening Agent',
  outreach: 'Outreach Agent',
  scheduling: 'Scheduling Agent',
  evaluation: 'Evaluation Agent',
} as const;

// Workflow statuses
export const WORKFLOW_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

// Agent statuses
export const AGENT_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

// Polling interval (milliseconds)
export const POLLING_INTERVAL = 2000; // 2 seconds

// API endpoints
export const API_ENDPOINTS = {
  WORKFLOW: '/workflow',
  WORKFLOW_STATUS: (id: string) => `/workflow/${id}/status`,
  WORKFLOW_RESULTS: (id: string) => `/workflow/${id}/results`,
  JOBS: (id: string) => `/jobs/${id}`,
  HEALTH: '/health',
} as const;

// Common skills for autocomplete
export const COMMON_SKILLS = [
  'Python',
  'JavaScript',
  'TypeScript',
  'React',
  'Node.js',
  'AWS',
  'Docker',
  'Kubernetes',
  'SQL',
  'NoSQL',
  'MongoDB',
  'PostgreSQL',
  'Redis',
  'GraphQL',
  'REST API',
  'Git',
  'CI/CD',
  'Agile',
  'Scrum',
  'Java',
  'C++',
  'Go',
  'Rust',
  'Ruby',
  'PHP',
  'Swift',
  'Kotlin',
  'Machine Learning',
  'Data Science',
  'TensorFlow',
  'PyTorch',
];

// Experience ranges
export const EXPERIENCE_RANGES = {
  MIN: 0,
  MAX: 20,
  STEP: 1,
} as const;

// Validation rules
export const VALIDATION = {
  JOB_TITLE: {
    MIN_LENGTH: 5,
    MAX_LENGTH: 100,
  },
  JOB_DESCRIPTION: {
    MIN_LENGTH: 50,
    MAX_LENGTH: 2000,
  },
  REQUIRED_SKILLS: {
    MIN_COUNT: 3,
  },
} as const;
