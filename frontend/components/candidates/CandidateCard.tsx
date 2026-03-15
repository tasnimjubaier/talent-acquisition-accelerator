'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { User, MapPin, Briefcase, Star } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * CandidateCard Component
 * 
 * Displays individual candidate information in a card format.
 * Shows name, location, experience, skills, and match score.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.4)
 */

interface CandidateCardProps {
  candidate: {
    id: string;
    name: string;
    location?: string;
    experience?: number;
    skills: string[];
    matchScore: number;
    summary?: string;
  };
  onClick?: () => void;
  showDetails?: boolean;
}

export default function CandidateCard({ 
  candidate, 
  onClick,
  showDetails = true 
}: CandidateCardProps) {
  // Determine score color
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 75) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  return (
    <Card 
      className={cn(
        'transition-all duration-200 hover:shadow-md',
        onClick && 'cursor-pointer'
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Candidate Info */}
          <div className="flex-1 min-w-0">
            {/* Name and Avatar */}
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <User className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-base truncate">{candidate.name}</h4>
                <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                  {candidate.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {candidate.location}
                    </span>
                  )}
                  {candidate.experience !== undefined && (
                    <span className="flex items-center gap-1">
                      <Briefcase className="h-3 w-3" />
                      {candidate.experience} years
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Summary */}
            {candidate.summary && (
              <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                {candidate.summary}
              </p>
            )}

            {/* Skills */}
            <div className="flex flex-wrap gap-1.5">
              {candidate.skills.slice(0, 5).map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
              {candidate.skills.length > 5 && (
                <Badge variant="outline" className="text-xs">
                  +{candidate.skills.length - 5} more
                </Badge>
              )}
            </div>
          </div>

          {/* Match Score */}
          <div className="flex flex-col items-center gap-2 flex-shrink-0">
            <div className={cn(
              'w-16 h-16 rounded-full border-2 flex flex-col items-center justify-center',
              getScoreColor(candidate.matchScore)
            )}>
              <Star className="h-4 w-4 mb-0.5" />
              <span className="text-lg font-bold">{candidate.matchScore}%</span>
            </div>
            <span className="text-xs text-muted-foreground">Match</span>
          </div>
        </div>

        {/* View Details Button */}
        {showDetails && onClick && (
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full mt-4"
            onClick={(e) => {
              e.stopPropagation();
              onClick();
            }}
          >
            View Details
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
