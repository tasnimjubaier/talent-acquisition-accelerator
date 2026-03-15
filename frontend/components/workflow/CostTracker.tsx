'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { DollarSign, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * CostTracker Component
 * 
 * Displays real-time cost tracking for the workflow.
 * Shows current cost, estimated total, breakdown by agent, and budget status.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.7)
 * - Cost optimization: 14_cost_optimization_strategy.md
 */

interface CostTrackerProps {
  currentCost: number;
  estimatedCost: number;
  budget?: number; // Optional budget limit
  breakdown?: {
    agent: string;
    cost: number;
  }[];
}

export default function CostTracker({ 
  currentCost, 
  estimatedCost, 
  budget = 5.0, // Default $5 per workflow
  breakdown = [] 
}: CostTrackerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate percentages
  const progressPercentage = (currentCost / estimatedCost) * 100;
  const budgetPercentage = (currentCost / budget) * 100;
  const remaining = budget - currentCost;

  // Determine status color
  const getStatusColor = () => {
    if (budgetPercentage >= 90) return 'text-destructive';
    if (budgetPercentage >= 70) return 'text-yellow-600';
    return 'text-green-600';
  };

  // Format currency
  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Cost Tracker
          </CardTitle>
          <Badge variant={budgetPercentage >= 90 ? 'destructive' : 'secondary'}>
            {budgetPercentage.toFixed(0)}% of budget
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current Cost */}
        <div>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-sm text-muted-foreground">Current Cost</span>
            <span className={cn('text-2xl font-bold', getStatusColor())}>
              {formatCost(currentCost)}
            </span>
          </div>
          
          {/* Progress Bar */}
          <Progress value={progressPercentage} className="h-2" />
          
          <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
            <span>Estimated: {formatCost(estimatedCost)}</span>
            <span>Budget: {formatCost(budget)}</span>
          </div>
        </div>

        {/* Budget Status */}
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center gap-2">
            <TrendingUp className={cn('h-4 w-4', getStatusColor())} />
            <span className="text-sm font-medium">Budget Remaining</span>
          </div>
          <span className={cn('text-sm font-bold', getStatusColor())}>
            {formatCost(remaining)}
          </span>
        </div>

        {/* Breakdown Toggle */}
        {breakdown.length > 0 && (
          <div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center justify-between w-full text-sm font-medium hover:text-primary transition-colors"
            >
              <span>Cost Breakdown by Agent</span>
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>

            {/* Breakdown Details */}
            {isExpanded && (
              <div className="mt-3 space-y-2">
                {breakdown.map((item) => (
                  <div 
                    key={item.agent}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-muted-foreground">{item.agent}</span>
                    <span className="font-medium">{formatCost(item.cost)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Warning Message */}
        {budgetPercentage >= 90 && (
          <div className="p-3 bg-destructive/10 border border-destructive rounded-lg">
            <p className="text-xs text-destructive font-medium">
              ⚠️ Approaching budget limit
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
