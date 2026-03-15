'use client';

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  BarChart3,
  Users,
  Mail,
  Calendar,
  Award,
  Download,
  Share2,
} from 'lucide-react';
import { TopCandidatesRanking } from './TopCandidatesRanking';
import { SkillMatchChart } from './SkillMatchChart';
import { OutreachPreview } from './OutreachPreview';
import { InterviewSchedule } from './InterviewSchedule';
import { FinalRecommendations } from './FinalRecommendations';
import { CandidatePipeline } from '../candidates/CandidatePipeline';

/**
 * ResultsVisualization Component
 * 
 * Main orchestrator for the results page. Integrates all results components
 * with tab navigation for different views (Overview, Candidates, Outreach, Schedule, Recommendations).
 * 
 * Reference: 00_frontend_specification.md - Results Visualization
 * Reference: 11_user_experience_design.md - Results page UX
 */

interface ResultsVisualizationProps {
  workflowId: string;
  jobTitle: string;
  topCandidates: any[];
  allCandidates: any[];
  skillMatchData: any[];
  outreachMessages: any[];
  interviews: any[];
  recommendations: any[];
  workflowStats: {
    totalCandidates: number;
    qualifiedCandidates: number;
    interviewsScheduled: number;
    totalCost: number;
    duration: number; // seconds
  };
}

type TabType = 'overview' | 'candidates' | 'outreach' | 'schedule' | 'recommendations';

export function ResultsVisualization({
  workflowId,
  jobTitle,
  topCandidates,
  allCandidates,
  skillMatchData,
  outreachMessages,
  interviews,
  recommendations,
  workflowStats,
}: ResultsVisualizationProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Tab configuration
  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'candidates' as TabType, label: 'Candidates', icon: Users },
    { id: 'outreach' as TabType, label: 'Outreach', icon: Mail },
    { id: 'schedule' as TabType, label: 'Schedule', icon: Calendar },
    { id: 'recommendations' as TabType, label: 'Recommendations', icon: Award },
  ];

  // Format duration
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m ${seconds % 60}s`;
  };

  // Export results
  const handleExport = () => {
    // TODO: Implement export functionality (CSV/PDF)
    console.log('Exporting results...');
  };

  // Share results
  const handleShare = () => {
    // TODO: Implement share functionality
    console.log('Sharing results...');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Results: {jobTitle}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Workflow ID: {workflowId}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={handleShare}>
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {workflowStats.totalCandidates}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Total Candidates
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                {workflowStats.qualifiedCandidates}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Qualified
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                {workflowStats.interviewsScheduled}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Interviews
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                ${workflowStats.totalCost.toFixed(2)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Total Cost
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-600 dark:text-gray-400">
                {formatDuration(workflowStats.duration)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Duration
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex gap-2 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="font-medium">{tab.label}</span>
                {/* Badge counts */}
                {tab.id === 'candidates' && (
                  <Badge variant="secondary">{allCandidates.length}</Badge>
                )}
                {tab.id === 'outreach' && (
                  <Badge variant="secondary">{outreachMessages.length}</Badge>
                )}
                {tab.id === 'schedule' && (
                  <Badge variant="secondary">{interviews.length}</Badge>
                )}
                {tab.id === 'recommendations' && (
                  <Badge variant="secondary">{recommendations.length}</Badge>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <TopCandidatesRanking candidates={topCandidates} />
            
            <div className="grid md:grid-cols-2 gap-6">
              {topCandidates.length > 0 && skillMatchData.length > 0 && (
                <SkillMatchChart
                  candidateName={topCandidates[0].name}
                  skills={skillMatchData}
                />
              )}
              
              {outreachMessages.length > 0 && (
                <OutreachPreview messages={outreachMessages.slice(0, 3)} />
              )}
            </div>

            {interviews.length > 0 && (
              <InterviewSchedule interviews={interviews} />
            )}
          </div>
        )}

        {/* Candidates Tab */}
        {activeTab === 'candidates' && (
          <CandidatePipeline candidates={allCandidates} />
        )}

        {/* Outreach Tab */}
        {activeTab === 'outreach' && (
          <OutreachPreview messages={outreachMessages} />
        )}

        {/* Schedule Tab */}
        {activeTab === 'schedule' && (
          <InterviewSchedule interviews={interviews} />
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <FinalRecommendations recommendations={recommendations} />
        )}
      </div>
    </div>
  );
}
