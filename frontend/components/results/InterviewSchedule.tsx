'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar, Clock, MapPin, User, Video, ChevronLeft, ChevronRight } from 'lucide-react';

/**
 * InterviewSchedule Component
 * 
 * Displays scheduled interviews in a calendar/timeline view.
 * Shows candidate-interviewer matching, time slots, and location/format.
 * Handles timezone display and navigation between dates.
 * 
 * Reference: 00_frontend_specification.md - Results Visualization
 * Reference: 08_agent_specifications.md - Scheduling Agent
 */

interface Interview {
  id: string;
  candidateName: string;
  candidateEmail: string;
  interviewerName: string;
  interviewerTitle: string;
  date: string; // ISO date string
  startTime: string; // HH:MM format
  endTime: string; // HH:MM format
  duration: number; // minutes
  timezone: string;
  format: 'in-person' | 'video' | 'phone';
  location?: string; // For in-person or video link
  type: 'technical' | 'behavioral' | 'cultural' | 'final';
  status: 'scheduled' | 'confirmed' | 'pending';
}

interface InterviewScheduleProps {
  interviews: Interview[];
  className?: string;
}

export function InterviewSchedule({ interviews, className = '' }: InterviewScheduleProps) {
  // Group interviews by date
  const interviewsByDate = interviews.reduce((acc, interview) => {
    const date = interview.date;
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(interview);
    return acc;
  }, {} as Record<string, Interview[]>);

  // Sort dates
  const sortedDates = Object.keys(interviewsByDate).sort();
  
  const [currentDateIndex, setCurrentDateIndex] = useState(0);
  const currentDate = sortedDates[currentDateIndex] || null;
  const currentInterviews = currentDate ? interviewsByDate[currentDate] : [];

  // Navigation
  const goToPreviousDate = () => {
    if (currentDateIndex > 0) {
      setCurrentDateIndex(currentDateIndex - 1);
    }
  };

  const goToNextDate = () => {
    if (currentDateIndex < sortedDates.length - 1) {
      setCurrentDateIndex(currentDateIndex + 1);
    }
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Get format icon
  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'video':
        return <Video className="h-4 w-4" />;
      case 'in-person':
        return <MapPin className="h-4 w-4" />;
      case 'phone':
        return <Clock className="h-4 w-4" />;
      default:
        return <Calendar className="h-4 w-4" />;
    }
  };

  // Get type color
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'technical':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
      case 'behavioral':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      case 'cultural':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300';
      case 'final':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      case 'scheduled':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Interview Schedule</CardTitle>
        <CardDescription>
          Scheduled interviews with candidates ({interviews.length} total)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {interviews.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No interviews scheduled yet</p>
          </div>
        ) : (
          <>
            {/* Date Navigation */}
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="outline"
                size="sm"
                onClick={goToPreviousDate}
                disabled={currentDateIndex === 0}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {currentDate ? formatDate(currentDate) : 'No date selected'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {currentInterviews.length} interview{currentInterviews.length !== 1 ? 's' : ''}
                </p>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={goToNextDate}
                disabled={currentDateIndex === sortedDates.length - 1}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            {/* Date Indicators */}
            <div className="flex justify-center gap-2 mb-6">
              {sortedDates.map((date, idx) => (
                <button
                  key={date}
                  onClick={() => setCurrentDateIndex(idx)}
                  className={`h-2 w-2 rounded-full transition-all ${
                    idx === currentDateIndex
                      ? 'bg-blue-600 w-6'
                      : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                  aria-label={`Go to ${formatDate(date)}`}
                />
              ))}
            </div>

            {/* Interviews Timeline */}
            <div className="space-y-4">
              {currentInterviews
                .sort((a, b) => a.startTime.localeCompare(b.startTime))
                .map((interview) => (
                  <div
                    key={interview.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    {/* Time and Status */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-gray-500" />
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-gray-100">
                            {interview.startTime} - {interview.endTime}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {interview.duration} min • {interview.timezone}
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(interview.status)}>
                        {interview.status}
                      </Badge>
                    </div>

                    {/* Candidate Info */}
                    <div className="flex items-center gap-2 mb-2">
                      <User className="h-4 w-4 text-gray-500" />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-gray-100">
                          {interview.candidateName}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {interview.candidateEmail}
                        </p>
                      </div>
                    </div>

                    {/* Interviewer Info */}
                    <div className="flex items-center gap-2 mb-3">
                      <User className="h-4 w-4 text-gray-500" />
                      <div>
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                          with <span className="font-medium">{interview.interviewerName}</span>
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {interview.interviewerTitle}
                        </p>
                      </div>
                    </div>

                    {/* Format and Location */}
                    <div className="flex items-center gap-4 mb-3">
                      <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                        {getFormatIcon(interview.format)}
                        <span className="capitalize">{interview.format}</span>
                      </div>
                      {interview.location && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                          {interview.location}
                        </p>
                      )}
                    </div>

                    {/* Type Badge */}
                    <Badge className={getTypeColor(interview.type)}>
                      {interview.type} interview
                    </Badge>
                  </div>
                ))}
            </div>

            {/* Summary Stats */}
            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                    {interviews.length}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Total</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-green-600 dark:text-green-400">
                    {interviews.filter(i => i.status === 'confirmed').length}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Confirmed</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-purple-600 dark:text-purple-400">
                    {interviews.filter(i => i.format === 'video').length}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Video</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-orange-600 dark:text-orange-400">
                    {sortedDates.length}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Days</p>
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
