'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  TrendingUp,
  Award,
  CheckCircle2,
  XCircle,
  MinusCircle,
} from 'lucide-react';

/**
 * FinalRecommendations Component
 * 
 * Displays AI-generated hiring recommendations from the Evaluation Agent.
 * Shows consensus assessment, confidence scores, and actionable next steps.
 * 
 * Reference: 00_frontend_specification.md - Results Visualization
 * Reference: 08_agent_specifications.md - Evaluation Agent
 */

interface Recommendation {
  candidateId: string;
  candidateName: string;
  decision: 'strong_hire' | 'hire' | 'maybe' | 'no_hire';
  confidence: number; // 0-100
  overallScore: number; // 0-100
  strengths: string[];
  concerns: string[];
  reasoning: string;
  nextSteps: string[];
  consensusLevel: 'unanimous' | 'strong' | 'moderate' | 'weak';
}

interface FinalRecommendationsProps {
  recommendations: Recommendation[];
  className?: string;
}

export function FinalRecommendations({ recommendations, className = '' }: FinalRecommendationsProps) {
  // Sort by decision priority and confidence
  const sortedRecommendations = [...recommendations].sort((a, b) => {
    const decisionOrder = { strong_hire: 0, hire: 1, maybe: 2, no_hire: 3 };
    const orderDiff = decisionOrder[a.decision] - decisionOrder[b.decision];
    if (orderDiff !== 0) return orderDiff;
    return b.confidence - a.confidence;
  });

  // Get decision icon
  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'strong_hire':
        return <Award className="h-5 w-5" />;
      case 'hire':
        return <CheckCircle2 className="h-5 w-5" />;
      case 'maybe':
        return <MinusCircle className="h-5 w-5" />;
      case 'no_hire':
        return <XCircle className="h-5 w-5" />;
      default:
        return <AlertCircle className="h-5 w-5" />;
    }
  };

  // Get decision color
  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'strong_hire':
        return 'bg-green-600 text-white dark:bg-green-500';
      case 'hire':
        return 'bg-blue-600 text-white dark:bg-blue-500';
      case 'maybe':
        return 'bg-yellow-600 text-white dark:bg-yellow-500';
      case 'no_hire':
        return 'bg-red-600 text-white dark:bg-red-500';
      default:
        return 'bg-gray-600 text-white dark:bg-gray-500';
    }
  };

  // Get decision label
  const getDecisionLabel = (decision: string) => {
    switch (decision) {
      case 'strong_hire':
        return 'Strong Hire';
      case 'hire':
        return 'Hire';
      case 'maybe':
        return 'Maybe';
      case 'no_hire':
        return 'No Hire';
      default:
        return 'Unknown';
    }
  };

  // Get consensus color
  const getConsensusColor = (consensus: string) => {
    switch (consensus) {
      case 'unanimous':
        return 'text-green-600 dark:text-green-400';
      case 'strong':
        return 'text-blue-600 dark:text-blue-400';
      case 'moderate':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'weak':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  // Calculate summary stats
  const stats = {
    strongHire: recommendations.filter(r => r.decision === 'strong_hire').length,
    hire: recommendations.filter(r => r.decision === 'hire').length,
    maybe: recommendations.filter(r => r.decision === 'maybe').length,
    noHire: recommendations.filter(r => r.decision === 'no_hire').length,
    avgConfidence: Math.round(
      recommendations.reduce((sum, r) => sum + r.confidence, 0) / recommendations.length
    ),
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Final Hiring Recommendations</CardTitle>
        <CardDescription>
          AI-powered evaluation and consensus assessment
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="text-center p-3 bg-green-50 dark:bg-green-950 rounded-lg">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {stats.strongHire}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">Strong Hire</p>
          </div>
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {stats.hire}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">Hire</p>
          </div>
          <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {stats.maybe}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">Maybe</p>
          </div>
          <div className="text-center p-3 bg-red-50 dark:bg-red-950 rounded-lg">
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
              {stats.noHire}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">No Hire</p>
          </div>
          <div className="text-center p-3 bg-purple-50 dark:bg-purple-950 rounded-lg">
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {stats.avgConfidence}%
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">Avg Confidence</p>
          </div>
        </div>

        {/* Recommendations List */}
        <div className="space-y-4">
          {sortedRecommendations.map((rec) => (
            <div
              key={rec.candidateId}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    {rec.candidateName}
                  </h4>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge className={getDecisionColor(rec.decision)}>
                      <span className="flex items-center gap-1">
                        {getDecisionIcon(rec.decision)}
                        {getDecisionLabel(rec.decision)}
                      </span>
                    </Badge>
                    <span className={`text-sm font-medium ${getConsensusColor(rec.consensusLevel)}`}>
                      {rec.consensusLevel} consensus
                    </span>
                  </div>
                </div>
                <div className="text-right ml-4">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {rec.overallScore}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Overall Score</p>
                </div>
              </div>

              {/* Confidence */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Confidence Level
                  </span>
                  <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                    {rec.confidence}%
                  </span>
                </div>
                <Progress value={rec.confidence} className="h-2" />
              </div>

              {/* Reasoning */}
              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded">
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {rec.reasoning}
                </p>
              </div>

              {/* Strengths and Concerns */}
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                {/* Strengths */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <ThumbsUp className="h-4 w-4 text-green-600 dark:text-green-400" />
                    <h5 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      Strengths
                    </h5>
                  </div>
                  <ul className="space-y-1">
                    {rec.strengths.map((strength, idx) => (
                      <li
                        key={idx}
                        className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2"
                      >
                        <span className="text-green-600 dark:text-green-400 mt-1">•</span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Concerns */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <ThumbsDown className="h-4 w-4 text-red-600 dark:text-red-400" />
                    <h5 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      Concerns
                    </h5>
                  </div>
                  <ul className="space-y-1">
                    {rec.concerns.length > 0 ? (
                      rec.concerns.map((concern, idx) => (
                        <li
                          key={idx}
                          className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2"
                        >
                          <span className="text-red-600 dark:text-red-400 mt-1">•</span>
                          <span>{concern}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-sm text-gray-500 dark:text-gray-400 italic">
                        No major concerns identified
                      </li>
                    )}
                  </ul>
                </div>
              </div>

              {/* Next Steps */}
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <h5 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Recommended Next Steps
                  </h5>
                </div>
                <div className="flex flex-wrap gap-2">
                  {rec.nextSteps.map((step, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {step}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mt-4">
                <Button size="sm" variant="default">
                  View Full Profile
                </Button>
                <Button size="sm" variant="outline">
                  Schedule Follow-up
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
