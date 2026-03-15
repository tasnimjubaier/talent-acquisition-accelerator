'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Briefcase, MapPin, Clock } from 'lucide-react';

/**
 * JobSummaryCard Component
 * 
 * Displays a summary of the job posting in workflow and results pages.
 * Shows key information like title, location, skills, and experience requirements.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 4.2)
 */

interface JobSummaryCardProps {
  job: {
    jobTitle: string;
    location?: string;
    remote?: boolean;
    requiredSkills: string[];
    preferredSkills?: string[];
    experienceMin: number;
    experienceMax: number;
  };
}

export default function JobSummaryCard({ job }: JobSummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-2xl">{job.jobTitle}</CardTitle>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {/* Location */}
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                <span>{job.remote ? 'Remote' : job.location || 'Not specified'}</span>
              </div>
              
              {/* Experience */}
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>
                  {job.experienceMin}-{job.experienceMax} years
                </span>
              </div>
            </div>
          </div>
          
          <Briefcase className="h-8 w-8 text-muted-foreground" />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Required Skills */}
        <div>
          <h4 className="text-sm font-medium mb-2">Required Skills</h4>
          <div className="flex flex-wrap gap-2">
            {job.requiredSkills.map((skill) => (
              <Badge key={skill} variant="default">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
        
        {/* Preferred Skills */}
        {job.preferredSkills && job.preferredSkills.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2">Preferred Skills</h4>
            <div className="flex flex-wrap gap-2">
              {job.preferredSkills.map((skill) => (
                <Badge key={skill} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
