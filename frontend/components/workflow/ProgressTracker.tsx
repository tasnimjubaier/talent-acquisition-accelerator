'use client';

import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

/**
 * ProgressTracker Component
 * 
 * Visual progress indicator showing the workflow stages.
 * Displays current stage, completed stages, and upcoming stages.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 4.2)
 * - Progress indicators: https://www.radix-ui.com/primitives/docs/components/progress
 */

interface ProgressTrackerProps {
  currentStep: number; // 0-4 (Sourcing, Screening, Outreach, Scheduling, Evaluation)
  steps: string[];
}

export default function ProgressTracker({ currentStep, steps }: ProgressTrackerProps) {
  return (
    <div className="w-full">
      {/* Progress Bar */}
      <div className="relative">
        {/* Background Line */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-muted" />
        
        {/* Progress Line */}
        <div 
          className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500"
          style={{ 
            width: `${(currentStep / (steps.length - 1)) * 100}%` 
          }}
        />

        {/* Steps */}
        <div className="relative flex justify-between">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            const isPending = index > currentStep;

            return (
              <div key={step} className="flex flex-col items-center">
                {/* Step Circle */}
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300',
                  isCompleted && 'bg-primary border-primary',
                  isCurrent && 'bg-primary border-primary animate-pulse',
                  isPending && 'bg-background border-muted'
                )}>
                  {isCompleted && (
                    <CheckCircle2 className="h-5 w-5 text-primary-foreground" />
                  )}
                  {isCurrent && (
                    <Loader2 className="h-5 w-5 text-primary-foreground animate-spin" />
                  )}
                  {isPending && (
                    <Circle className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>

                {/* Step Label */}
                <div className="mt-2 text-center">
                  <p className={cn(
                    'text-xs font-medium transition-colors',
                    (isCompleted || isCurrent) && 'text-foreground',
                    isPending && 'text-muted-foreground'
                  )}>
                    {step}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Progress Percentage */}
      <div className="mt-6 text-center">
        <p className="text-sm text-muted-foreground">
          Progress: {Math.round((currentStep / (steps.length - 1)) * 100)}%
        </p>
      </div>
    </div>
  );
}
