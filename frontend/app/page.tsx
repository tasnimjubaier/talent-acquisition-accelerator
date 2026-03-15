'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import JobPostingForm from '@/components/job/JobPostingForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkles, Users, Zap, Target } from 'lucide-react';

/**
 * Home Page - Job Posting Creation
 * 
 * Main entry point for the Talent Acquisition Accelerator.
 * Users create job postings here to start the AI-powered recruitment workflow.
 * 
 * Features:
 * - Hero section with product overview
 * - Feature highlights
 * - Job posting form (JobPostingForm component)
 * - Automatic navigation to workflow page on submission
 * 
 * Related Governing Docs:
 * - 00_frontend_specification.md - Page requirements
 * - 11_user_experience_design.md - UX flow
 */
export default function Home() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleJobSubmit = async (jobData: any) => {
    setIsSubmitting(true);
    try {
      // API call will be handled by JobPostingForm
      // This callback receives the workflow ID and navigates
      const workflowId = jobData.workflowId;
      
      // Navigate to workflow status page
      router.push(`/workflow/${workflowId}`);
    } catch (error) {
      console.error('Error starting workflow:', error);
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="space-y-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            Powered by Amazon Nova AI
          </div>
          
          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
            Talent Acquisition Accelerator
          </h1>
          
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            AI-powered recruiting pipeline using multi-agent system to source, screen, 
            and engage top talent in minutes, not weeks.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-12">
          <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <CardTitle className="text-lg">Lightning Fast</CardTitle>
              <CardDescription>
                Process 100+ candidates in under 2 minutes with AI-powered screening
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-primary" />
              </div>
              <CardTitle className="text-lg">Precision Matching</CardTitle>
              <CardDescription>
                Multi-dimensional scoring across skills, experience, and cultural fit
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-primary" />
              </div>
              <CardTitle className="text-lg">5 AI Agents</CardTitle>
              <CardDescription>
                Specialized agents for sourcing, screening, outreach, scheduling, and evaluation
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Job Posting Form Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-3">Create a Job Posting</h2>
            <p className="text-muted-foreground">
              Fill in the details below to start your AI-powered recruitment workflow
            </p>
          </div>

          <JobPostingForm 
            onSubmit={handleJobSubmit}
            isSubmitting={isSubmitting}
          />
        </div>
      </section>

      {/* How It Works Section */}
      <section className="container mx-auto px-4 py-16 bg-muted/50 rounded-lg mb-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          
          <div className="space-y-8">
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Create Job Posting</h3>
                <p className="text-muted-foreground">
                  Define your role requirements, skills, and preferences. Our AI understands context and nuance.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">AI Agents Process</h3>
                <p className="text-muted-foreground">
                  Five specialized agents work in parallel: sourcing candidates, screening qualifications, 
                  crafting personalized outreach, scheduling interviews, and generating recommendations.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Review Results</h3>
                <p className="text-muted-foreground">
                  Get ranked candidates with detailed insights, personalized outreach messages, 
                  and interview schedules ready to go.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
