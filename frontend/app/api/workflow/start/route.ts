/**
 * Next.js API Route: Start Workflow
 * 
 * POST /api/workflow/start
 * 
 * Optional middleware layer between frontend and AWS API Gateway.
 * Can be used for:
 * - Request validation
 * - Rate limiting
 * - Logging
 * - Error transformation
 * 
 * For direct AWS integration, frontend can call API Gateway directly.
 */

import { NextRequest, NextResponse } from 'next/server';
import ApiGatewayService from '@/lib/api-gateway';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate request
    if (!body.jobTitle || !body.jobDescription) {
      return NextResponse.json(
        { error: 'Missing required fields: jobTitle, jobDescription' },
        { status: 400 }
      );
    }

    // Call AWS API Gateway
    const response = await ApiGatewayService.startWorkflow(body);

    return NextResponse.json(response, { status: 200 });
  } catch (error: any) {
    console.error('Error starting workflow:', error);
    
    return NextResponse.json(
      { error: error.message || 'Failed to start workflow' },
      { status: 500 }
    );
  }
}
