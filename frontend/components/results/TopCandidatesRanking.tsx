'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { User, Trophy, Medal, Award } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * TopCandidatesRanking Component
 * 
 * Showcases the top 3 candidates in a podium-style layout.
 * Displays match scores, key skills, and provides quick access to details.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.5)
 * - Podium design patterns: https://dribbble.com/tags/podium
 */

interface Candidate {
  id: string;
  name: string;
  matchScore: number;
  skills: string[];
  summary?: string;
  location?: string;
  experience?: number;
}

interface TopCandidatesRankingProps {
  candidates: Candidate[];
  onViewDetails?: (candidate: Candidate) => void;
}

const rankIcons = [Trophy, Medal, Award];
const rankColors = [
  'text-yellow-600 bg-yellow-50 border-yellow-200',
  'text-gray-600 bg-gray-50 border-gray-200',
  'text-orange-600 bg-orange-50 border-orange-200'
];
const rankLabels = ['1st Place', '2nd Place', '3rd Place'];

export default function TopCandidatesRanking({ 
  candidates, 
  onViewDetails 
}: TopCandidatesRankingProps) {
  // Get top 3 candidates
  const topThree = candidates
    .sort((a, b) => b.matchScore - a.matchScore)
    .slice(0, 3);

  if (topThree.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>No candidates available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Top Candidates</h2>
        <p className="text-muted-foreground">
          Best matches based on skills, experience, and requirements
        </p>
      </div>

      {/* Podium Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
        {/* 2nd Place (Left) */}
        {topThree[1] && (
          <div className="md:order-1 order-2">
            <CandidateRankCard
              candidate={topThree[1]}
              rank={1}
              onViewDetails={onViewDetails}
            />
          </div>
        )}

        {/* 1st Place (Center, Elevated) */}
        {topThree[0] && (
          <div className="md:order-2 order-1 md:scale-110 md:mb-6">
            <CandidateRankCard
              candidate={topThree[0]}
              rank={0}
              onViewDetails={onViewDetails}
              isWinner
            />
          </div>
        )}

        {/* 3rd Place (Right) */}
        {topThree[2] && (
          <div className="md:order-3 order-3">
            <CandidateRankCard
              candidate={topThree[2]}
              rank={2}
              onViewDetails={onViewDetails}
            />
          </div>
        )}
      </div>
    </div>
  );
}

interface CandidateRankCardProps {
  candidate: Candidate;
  rank: number;
  onViewDetails?: (candidate: Candidate) => void;
  isWinner?: boolean;
}

function CandidateRankCard({ 
  candidate, 
  rank, 
  onViewDetails,
  isWinner = false 
}: CandidateRankCardProps) {
  const RankIcon = rankIcons[rank];

  return (
    <Card className={cn(
      'transition-all duration-300 hover:shadow-lg',
      isWinner && 'border-2 border-primary'
    )}>
      <CardContent className="p-6 text-center space-y-4">
        {/* Rank Badge */}
        <div className="flex justify-center">
          <div className={cn(
            'w-16 h-16 rounded-full border-2 flex items-center justify-center',
            rankColors[rank]
          )}>
            <RankIcon className="h-8 w-8" />
          </div>
        </div>

        {/* Rank Label */}
        <Badge 
          variant={isWinner ? 'default' : 'secondary'}
          className="text-xs"
        >
          {rankLabels[rank]}
        </Badge>

        {/* Avatar */}
        <div className="flex justify-center">
          <div className={cn(
            'w-20 h-20 rounded-full flex items-center justify-center',
            isWinner ? 'bg-primary/10' : 'bg-muted'
          )}>
            <User className={cn(
              'h-10 w-10',
              isWinner ? 'text-primary' : 'text-muted-foreground'
            )} />
          </div>
        </div>

        {/* Name */}
        <h3 className="font-bold text-lg">{candidate.name}</h3>

        {/* Match Score */}
        <div>
          <div className={cn(
            'text-4xl font-bold',
            isWinner ? 'text-primary' : 'text-foreground'
          )}>
            {candidate.matchScore}%
          </div>
          <p className="text-sm text-muted-foreground">Match Score</p>
        </div>

        {/* Key Skills */}
        <div className="flex flex-wrap gap-1.5 justify-center">
          {candidate.skills.slice(0, 4).map((skill) => (
            <Badge key={skill} variant="outline" className="text-xs">
              {skill}
            </Badge>
          ))}
          {candidate.skills.length > 4 && (
            <Badge variant="outline" className="text-xs">
              +{candidate.skills.length - 4}
            </Badge>
          )}
        </div>

        {/* Summary */}
        {candidate.summary && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {candidate.summary}
          </p>
        )}

        {/* View Details Button */}
        {onViewDetails && (
          <Button
            variant={isWinner ? 'default' : 'outline'}
            className="w-full"
            onClick={() => onViewDetails(candidate)}
          >
            View Full Profile
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
