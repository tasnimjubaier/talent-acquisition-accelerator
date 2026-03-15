'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, X } from 'lucide-react';

/**
 * JobPostingForm Component
 * 
 * Main form for creating job postings and initiating the recruiting pipeline.
 * Implements validation, skill management, and API integration.
 * 
 * References:
 * - Frontend Spec: 00_frontend_specification.md (Section 5.1)
 * - React Hook Form patterns: https://react-hook-form.com/
 * - Form validation: https://nextjs.org/docs/app/building-your-application/data-fetching/forms-and-mutations
 */

interface JobPostingFormData {
  jobTitle: string;
  jobDescription: string;
  requiredSkills: string[];
  preferredSkills: string[];
  experienceMin: number;
  experienceMax: number;
  location: string;
  remote: boolean;
}

interface JobPostingFormProps {
  onSubmit?: (data: JobPostingFormData) => Promise<void>;
  isDemo?: boolean;
}

export default function JobPostingForm({ onSubmit, isDemo = false }: JobPostingFormProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Form state
  const [formData, setFormData] = useState<JobPostingFormData>({
    jobTitle: '',
    jobDescription: '',
    requiredSkills: [],
    preferredSkills: [],
    experienceMin: 0,
    experienceMax: 5,
    location: '',
    remote: false,
  });

  // Skill input states
  const [requiredSkillInput, setRequiredSkillInput] = useState('');
  const [preferredSkillInput, setPreferredSkillInput] = useState('');

  /**
   * Validate form data
   * Rules from frontend spec section 5.1
   */
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Job title validation
    if (!formData.jobTitle.trim()) {
      newErrors.jobTitle = 'Job title is required';
    } else if (formData.jobTitle.length < 5 || formData.jobTitle.length > 100) {
      newErrors.jobTitle = 'Job title must be between 5 and 100 characters';
    }

    // Job description validation
    if (!formData.jobDescription.trim()) {
      newErrors.jobDescription = 'Job description is required';
    } else if (formData.jobDescription.length < 50) {
      newErrors.jobDescription = 'Job description must be at least 50 characters';
    } else if (formData.jobDescription.length > 2000) {
      newErrors.jobDescription = 'Job description must not exceed 2000 characters';
    }

    // Required skills validation
    if (formData.requiredSkills.length < 3) {
      newErrors.requiredSkills = 'At least 3 required skills are needed';
    }

    // Experience range validation
    if (formData.experienceMin < 0 || formData.experienceMin > 20) {
      newErrors.experienceMin = 'Minimum experience must be between 0 and 20 years';
    }
    if (formData.experienceMax < 0 || formData.experienceMax > 20) {
      newErrors.experienceMax = 'Maximum experience must be between 0 and 20 years';
    }
    if (formData.experienceMin >= formData.experienceMax) {
      newErrors.experienceRange = 'Minimum experience must be less than maximum';
    }

    // Location validation (if not remote)
    if (!formData.remote && !formData.location.trim()) {
      newErrors.location = 'Location is required for non-remote positions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Add skill to required skills list
   */
  const addRequiredSkill = () => {
    const skill = requiredSkillInput.trim();
    if (skill && !formData.requiredSkills.includes(skill)) {
      setFormData({
        ...formData,
        requiredSkills: [...formData.requiredSkills, skill],
      });
      setRequiredSkillInput('');
      // Clear error if we now have enough skills
      if (formData.requiredSkills.length + 1 >= 3) {
        setErrors({ ...errors, requiredSkills: '' });
      }
    }
  };

  /**
   * Remove skill from required skills list
   */
  const removeRequiredSkill = (skill: string) => {
    setFormData({
      ...formData,
      requiredSkills: formData.requiredSkills.filter((s) => s !== skill),
    });
  };

  /**
   * Add skill to preferred skills list
   */
  const addPreferredSkill = () => {
    const skill = preferredSkillInput.trim();
    if (skill && !formData.preferredSkills.includes(skill)) {
      setFormData({
        ...formData,
        preferredSkills: [...formData.preferredSkills, skill],
      });
      setPreferredSkillInput('');
    }
  };

  /**
   * Remove skill from preferred skills list
   */
  const removePreferredSkill = (skill: string) => {
    setFormData({
      ...formData,
      preferredSkills: formData.preferredSkills.filter((s) => s !== skill),
    });
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      if (onSubmit) {
        await onSubmit(formData);
      } else {
        // Default: Call API and redirect
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/workflow`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData),
        });

        if (!response.ok) {
          throw new Error('Failed to start workflow');
        }

        const data = await response.json();
        router.push(`/workflow/${data.workflowId}`);
      }
    } catch (error) {
      console.error('Form submission error:', error);
      setErrors({
        submit: 'Failed to start recruiting pipeline. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Load demo data
   */
  const loadDemoData = () => {
    setFormData({
      jobTitle: 'Senior Full-Stack Engineer',
      jobDescription: 'We are seeking an experienced Full-Stack Engineer to join our growing team. You will work on building scalable web applications using modern technologies. The ideal candidate has strong experience with React, Node.js, and cloud platforms. You will collaborate with product managers, designers, and other engineers to deliver high-quality features.',
      requiredSkills: ['React', 'Node.js', 'TypeScript', 'AWS', 'PostgreSQL'],
      preferredSkills: ['Next.js', 'GraphQL', 'Docker', 'Kubernetes'],
      experienceMin: 5,
      experienceMax: 10,
      location: 'San Francisco, CA',
      remote: true,
    });
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Create Job Posting</CardTitle>
        <CardDescription>
          Fill out the job requirements to start the AI-powered recruiting pipeline
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Demo Mode Button */}
          {isDemo && (
            <Button
              type="button"
              variant="outline"
              onClick={loadDemoData}
              className="w-full"
            >
              Load Demo Data
            </Button>
          )}

          {/* Job Title */}
          <div className="space-y-2">
            <Label htmlFor="jobTitle">
              Job Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="jobTitle"
              value={formData.jobTitle}
              onChange={(e) => setFormData({ ...formData, jobTitle: e.target.value })}
              placeholder="e.g., Senior Software Engineer"
              className={errors.jobTitle ? 'border-destructive' : ''}
            />
            {errors.jobTitle && (
              <p className="text-sm text-destructive">{errors.jobTitle}</p>
            )}
          </div>

          {/* Job Description */}
          <div className="space-y-2">
            <Label htmlFor="jobDescription">
              Job Description <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="jobDescription"
              value={formData.jobDescription}
              onChange={(e) => setFormData({ ...formData, jobDescription: e.target.value })}
              placeholder="Describe the role, responsibilities, and requirements..."
              rows={6}
              className={errors.jobDescription ? 'border-destructive' : ''}
            />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{formData.jobDescription.length} / 2000 characters</span>
              {formData.jobDescription.length < 50 && (
                <span className="text-destructive">
                  Minimum 50 characters required
                </span>
              )}
            </div>
            {errors.jobDescription && (
              <p className="text-sm text-destructive">{errors.jobDescription}</p>
            )}
          </div>

          {/* Required Skills */}
          <div className="space-y-2">
            <Label htmlFor="requiredSkills">
              Required Skills <span className="text-destructive">*</span>
              <span className="text-muted-foreground text-sm ml-2">(minimum 3)</span>
            </Label>
            <div className="flex gap-2">
              <Input
                id="requiredSkills"
                value={requiredSkillInput}
                onChange={(e) => setRequiredSkillInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addRequiredSkill();
                  }
                }}
                placeholder="Type a skill and press Enter"
                className={errors.requiredSkills ? 'border-destructive' : ''}
              />
              <Button
                type="button"
                onClick={addRequiredSkill}
                size="icon"
                variant="outline"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.requiredSkills.map((skill) => (
                <Badge key={skill} variant="default" className="gap-1">
                  {skill}
                  <button
                    type="button"
                    onClick={() => removeRequiredSkill(skill)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
            {errors.requiredSkills && (
              <p className="text-sm text-destructive">{errors.requiredSkills}</p>
            )}
          </div>

          {/* Preferred Skills */}
          <div className="space-y-2">
            <Label htmlFor="preferredSkills">Preferred Skills (Optional)</Label>
            <div className="flex gap-2">
              <Input
                id="preferredSkills"
                value={preferredSkillInput}
                onChange={(e) => setPreferredSkillInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addPreferredSkill();
                  }
                }}
                placeholder="Type a skill and press Enter"
              />
              <Button
                type="button"
                onClick={addPreferredSkill}
                size="icon"
                variant="outline"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.preferredSkills.map((skill) => (
                <Badge key={skill} variant="secondary" className="gap-1">
                  {skill}
                  <button
                    type="button"
                    onClick={() => removePreferredSkill(skill)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Experience Range */}
          <div className="space-y-2">
            <Label>
              Experience Range (years) <span className="text-destructive">*</span>
            </Label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="experienceMin" className="text-sm text-muted-foreground">
                  Minimum
                </Label>
                <Input
                  id="experienceMin"
                  type="number"
                  min="0"
                  max="20"
                  value={formData.experienceMin}
                  onChange={(e) =>
                    setFormData({ ...formData, experienceMin: parseInt(e.target.value) || 0 })
                  }
                  className={errors.experienceMin || errors.experienceRange ? 'border-destructive' : ''}
                />
              </div>
              <div>
                <Label htmlFor="experienceMax" className="text-sm text-muted-foreground">
                  Maximum
                </Label>
                <Input
                  id="experienceMax"
                  type="number"
                  min="0"
                  max="20"
                  value={formData.experienceMax}
                  onChange={(e) =>
                    setFormData({ ...formData, experienceMax: parseInt(e.target.value) || 0 })
                  }
                  className={errors.experienceMax || errors.experienceRange ? 'border-destructive' : ''}
                />
              </div>
            </div>
            {(errors.experienceMin || errors.experienceMax || errors.experienceRange) && (
              <p className="text-sm text-destructive">
                {errors.experienceMin || errors.experienceMax || errors.experienceRange}
              </p>
            )}
          </div>

          {/* Remote Toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="remote"
              checked={formData.remote}
              onChange={(e) => setFormData({ ...formData, remote: e.target.checked })}
              className="h-4 w-4"
            />
            <Label htmlFor="remote" className="cursor-pointer">
              Remote Position
            </Label>
          </div>

          {/* Location */}
          {!formData.remote && (
            <div className="space-y-2">
              <Label htmlFor="location">
                Location <span className="text-destructive">*</span>
              </Label>
              <Input
                id="location"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g., San Francisco, CA"
                className={errors.location ? 'border-destructive' : ''}
              />
              {errors.location && (
                <p className="text-sm text-destructive">{errors.location}</p>
              )}
            </div>
          )}

          {/* Submit Error */}
          {errors.submit && (
            <div className="p-4 bg-destructive/10 border border-destructive rounded-md">
              <p className="text-sm text-destructive">{errors.submit}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting Pipeline...
              </>
            ) : (
              'Start Recruiting Pipeline'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
