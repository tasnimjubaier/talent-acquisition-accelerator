import { useMemo } from 'react';
import { useWorkflowStore } from '@/store/workflowStore';
import type { Candidate } from '@/lib/types';

/**
 * Hook for filtering and sorting candidates
 */
export const useCandidates = (candidates: Candidate[] | undefined) => {
  const skillFilters = useWorkflowStore((state) => state.skillFilters);
  const experienceRange = useWorkflowStore((state) => state.experienceRange);
  
  const filteredCandidates = useMemo(() => {
    if (!candidates) return [];
    
    return candidates.filter((candidate) => {
      // Filter by skills
      if (skillFilters.length > 0) {
        const hasMatchingSkill = skillFilters.some((skill) =>
          candidate.skills.some((s) => 
            s.toLowerCase().includes(skill.toLowerCase())
          )
        );
        if (!hasMatchingSkill) return false;
      }
      
      // Filter by experience range
      const experience = candidate.yearsOfExperience || 0;
      if (experience < experienceRange[0] || experience > experienceRange[1]) {
        return false;
      }
      
      return true;
    });
  }, [candidates, skillFilters, experienceRange]);
  
  const sortedCandidates = useMemo(() => {
    return [...filteredCandidates].sort((a, b) => {
      // Sort by match score (descending)
      return (b.matchScore || 0) - (a.matchScore || 0);
    });
  }, [filteredCandidates]);
  
  const topCandidates = useMemo(() => {
    return sortedCandidates.slice(0, 3);
  }, [sortedCandidates]);
  
  const candidatesByScore = useMemo(() => {
    const excellent = sortedCandidates.filter((c) => (c.matchScore || 0) >= 90);
    const good = sortedCandidates.filter((c) => (c.matchScore || 0) >= 75 && (c.matchScore || 0) < 90);
    const fair = sortedCandidates.filter((c) => (c.matchScore || 0) >= 60 && (c.matchScore || 0) < 75);
    const poor = sortedCandidates.filter((c) => (c.matchScore || 0) < 60);
    
    return { excellent, good, fair, poor };
  }, [sortedCandidates]);
  
  return {
    allCandidates: sortedCandidates,
    topCandidates,
    candidatesByScore,
    totalCount: candidates?.length || 0,
    filteredCount: filteredCandidates.length,
  };
};

/**
 * Hook for candidate statistics
 */
export const useCandidateStats = (candidates: Candidate[] | undefined) => {
  return useMemo(() => {
    if (!candidates || candidates.length === 0) {
      return {
        averageScore: 0,
        averageExperience: 0,
        topSkills: [],
        experienceDistribution: [],
      };
    }
    
    // Average match score
    const averageScore = candidates.reduce((sum, c) => sum + (c.matchScore || 0), 0) / candidates.length;
    
    // Average experience
    const averageExperience = candidates.reduce((sum, c) => sum + (c.yearsOfExperience || 0), 0) / candidates.length;
    
    // Top skills (frequency count)
    const skillCounts: Record<string, number> = {};
    candidates.forEach((candidate) => {
      candidate.skills.forEach((skill) => {
        skillCounts[skill] = (skillCounts[skill] || 0) + 1;
      });
    });
    const topSkills = Object.entries(skillCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([skill, count]) => ({ skill, count }));
    
    // Experience distribution
    const experienceDistribution = [
      { range: '0-2 years', count: candidates.filter((c) => (c.yearsOfExperience || 0) <= 2).length },
      { range: '3-5 years', count: candidates.filter((c) => (c.yearsOfExperience || 0) >= 3 && (c.yearsOfExperience || 0) <= 5).length },
      { range: '6-10 years', count: candidates.filter((c) => (c.yearsOfExperience || 0) >= 6 && (c.yearsOfExperience || 0) <= 10).length },
      { range: '10+ years', count: candidates.filter((c) => (c.yearsOfExperience || 0) > 10).length },
    ];
    
    return {
      averageScore,
      averageExperience,
      topSkills,
      experienceDistribution,
    };
  }, [candidates]);
};
