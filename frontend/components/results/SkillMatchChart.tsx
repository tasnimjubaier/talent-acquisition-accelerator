'use client';

import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * SkillMatchChart Component
 * 
 * Displays a radar chart comparing candidate skills against job requirements.
 * Uses Recharts for visualization with interactive tooltips.
 * 
 * Reference: 00_frontend_specification.md - Results Visualization
 * Verification: https://recharts.org/en-US/examples/SimpleRadarChart
 */

interface SkillData {
  skill: string;
  required: number; // 0-100 scale
  candidate: number; // 0-100 scale
}

interface SkillMatchChartProps {
  candidateName: string;
  skills: SkillData[];
  className?: string;
}

export function SkillMatchChart({ candidateName, skills, className = '' }: SkillMatchChartProps) {
  // Calculate overall match percentage
  const overallMatch = skills.length > 0
    ? Math.round(
        skills.reduce((sum, skill) => sum + Math.min(skill.candidate / skill.required, 1), 0) /
          skills.length *
          100
      )
    : 0;

  // Custom tooltip for better UX
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-semibold text-sm mb-2">{payload[0].payload.skill}</p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            Required: {payload[0].value}%
          </p>
          <p className="text-sm text-green-600 dark:text-green-400">
            Candidate: {payload[1].value}%
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Match: {Math.round((payload[1].value / payload[0].value) * 100)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Skill Match Analysis</CardTitle>
        <CardDescription>
          {candidateName}&apos;s proficiency vs. job requirements
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Overall Match Score */}
        <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-950 dark:to-green-950 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Overall Skill Match
            </span>
            <span className="text-2xl font-bold text-green-600 dark:text-green-400">
              {overallMatch}%
            </span>
          </div>
        </div>

        {/* Radar Chart */}
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={skills}>
            <PolarGrid stroke="#e5e7eb" strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="skill"
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickLine={false}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#9ca3af', fontSize: 10 }}
              tickCount={6}
            />
            <Radar
              name="Required"
              dataKey="required"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <Radar
              name="Candidate"
              dataKey="candidate"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="circle"
            />
          </RadarChart>
        </ResponsiveContainer>

        {/* Skill Breakdown */}
        <div className="mt-6 space-y-2">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Skill Breakdown
          </h4>
          {skills.map((skill) => {
            const matchPercentage = Math.round((skill.candidate / skill.required) * 100);
            const isStrong = matchPercentage >= 100;
            const isGood = matchPercentage >= 80 && matchPercentage < 100;
            const isWeak = matchPercentage < 80;

            return (
              <div key={skill.skill} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 dark:text-gray-300 flex-1">
                  {skill.skill}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 dark:text-gray-400 text-xs">
                    {skill.candidate}% / {skill.required}%
                  </span>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      isStrong
                        ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                        : isGood
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                        : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                    }`}
                  >
                    {matchPercentage}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
