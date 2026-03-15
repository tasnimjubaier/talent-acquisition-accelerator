/**
 * Next.js API Route: Get Workflow Status
 * 
 * GET /api/workflow/[id]/status
 * 
 * Optional middleware layer for workflow status polling.
 */

import { NextRequest, NextResponse } from 'next/server';
import ApiGatewayService from '@/lib/api-gateway';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const workflowId = params.id;

    if (!workflowId) {
      return NextResponse.json(
        { error: 'Workflow ID is required' },
        { status: 400 }
      );
    }

    // Call AWS API Gateway
    const response = await ApiGatewayService.getWorkflowStatus(workflowId);

    return NextResponse.json(response, { status: 200 });
  } catch (error: any) {
    console.error('Error getting workflow status:', error);
    
    return NextResponse.json(
      { error: error.message || 'Failed to get workflow status' },
      { status: 500 }
    );
  }
}
