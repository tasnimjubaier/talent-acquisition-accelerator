'use client';

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import CandidateCard from './CandidateCard';
import { Search, SlidersHorizontal, Download, X } from 'lucide-react';

/**
 * CandidatePipeline Component
 * 
 * Displays a list of candidates with filtering, sorting, and search capabilities.
 * Supports pagination and CSV export.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.4)
 * - Filtering patterns: https://www.patterns.dev/posts/client-side-filtering
 */

interface Candidate {
  id: string;
  name: string;
  location?: string;
  experience?: number;
  skills: string[];
  matchScore: number;
  summary?: string;
}

interface CandidatePipelineProps {
  candidates: Candidate[];
  onCandidateClick?: (candidate: Candidate) => void;
  showFilters?: boolean;
}

type SortOption = 'score' | 'name' | 'experience';

export default function CandidatePipeline({ 
  candidates, 
  onCandidateClick,
  showFilters = true 
}: CandidatePipelineProps) {
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('score');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [experienceRange, setExperienceRange] = useState<[number, number]>([0, 20]);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Get all unique skills from candidates
  const allSkills = useMemo(() => {
    const skillSet = new Set<string>();
    candidates.forEach(c => c.skills.forEach(s => skillSet.add(s)));
    return Array.from(skillSet).sort();
  }, [candidates]);

  // Filter and sort candidates
  const filteredCandidates = useMemo(() => {
    let filtered = [...candidates];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(c => 
        c.name.toLowerCase().includes(query) ||
        c.skills.some(s => s.toLowerCase().includes(query)) ||
        c.summary?.toLowerCase().includes(query)
      );
    }

    // Skills filter
    if (selectedSkills.length > 0) {
      filtered = filtered.filter(c =>
        selectedSkills.some(skill => c.skills.includes(skill))
      );
    }

    // Experience filter
    filtered = filtered.filter(c => {
      if (c.experience === undefined) return true;
      return c.experience >= experienceRange[0] && c.experience <= experienceRange[1];
    });

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return b.matchScore - a.matchScore;
        case 'name':
          return a.name.localeCompare(b.name);
        case 'experience':
          return (b.experience || 0) - (a.experience || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [candidates, searchQuery, selectedSkills, experienceRange, sortBy]);

  // Pagination
  const totalPages = Math.ceil(filteredCandidates.length / itemsPerPage);
  const paginatedCandidates = filteredCandidates.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Toggle skill filter
  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['Name', 'Location', 'Experience', 'Skills', 'Match Score'];
    const rows = filteredCandidates.map(c => [
      c.name,
      c.location || '',
      c.experience?.toString() || '',
      c.skills.join('; '),
      c.matchScore.toString()
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'candidates.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Clear filters
  const clearFilters = () => {
    setSearchQuery('');
    setSelectedSkills([]);
    setExperienceRange([0, 20]);
    setCurrentPage(1);
  };

  const hasActiveFilters = searchQuery || selectedSkills.length > 0 || 
    experienceRange[0] !== 0 || experienceRange[1] !== 20;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            Candidates ({filteredCandidates.length})
          </h3>
          <p className="text-sm text-muted-foreground">
            {filteredCandidates.length !== candidates.length && 
              `Filtered from ${candidates.length} total`
            }
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Export Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={exportToCSV}
            disabled={filteredCandidates.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>

          {/* Filter Toggle */}
          {showFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilterPanel(!showFilterPanel)}
            >
              <SlidersHorizontal className="h-4 w-4 mr-2" />
              Filters
              {hasActiveFilters && (
                <Badge variant="destructive" className="ml-2 h-5 w-5 p-0 flex items-center justify-center">
                  !
                </Badge>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Search and Sort Bar */}
      <div className="flex gap-2">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, skills, or summary..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortOption)}
          className="px-3 py-2 border rounded-md bg-background text-sm"
        >
          <option value="score">Sort by Match Score</option>
          <option value="name">Sort by Name</option>
          <option value="experience">Sort by Experience</option>
        </select>
      </div>

      {/* Filter Panel */}
      {showFilters && showFilterPanel && (
        <div className="p-4 border rounded-lg bg-muted/50 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Filters</h4>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
              >
                <X className="h-4 w-4 mr-1" />
                Clear All
              </Button>
            )}
          </div>

          {/* Skills Filter */}
          <div>
            <label className="text-sm font-medium mb-2 block">Skills</label>
            <div className="flex flex-wrap gap-2">
              {allSkills.slice(0, 15).map(skill => (
                <Badge
                  key={skill}
                  variant={selectedSkills.includes(skill) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => toggleSkill(skill)}
                >
                  {skill}
                </Badge>
              ))}
            </div>
          </div>

          {/* Experience Range */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Experience: {experienceRange[0]}-{experienceRange[1]} years
            </label>
            <div className="flex gap-4">
              <Input
                type="number"
                min="0"
                max="20"
                value={experienceRange[0]}
                onChange={(e) => setExperienceRange([parseInt(e.target.value) || 0, experienceRange[1]])}
                className="w-20"
              />
              <span className="self-center">to</span>
              <Input
                type="number"
                min="0"
                max="20"
                value={experienceRange[1]}
                onChange={(e) => setExperienceRange([experienceRange[0], parseInt(e.target.value) || 20])}
                className="w-20"
              />
            </div>
          </div>
        </div>
      )}

      {/* Candidates Grid */}
      {paginatedCandidates.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {paginatedCandidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                onClick={onCandidateClick ? () => onCandidateClick(candidate) : undefined}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          <p>No candidates found matching your criteria</p>
          {hasActiveFilters && (
            <Button
              variant="link"
              onClick={clearFilters}
              className="mt-2"
            >
              Clear filters
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
