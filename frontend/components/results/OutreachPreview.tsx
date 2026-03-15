'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Mail, Linkedin, Copy, Check, MessageSquare } from 'lucide-react';

/**
 * OutreachPreview Component
 * 
 * Displays AI-generated outreach messages for candidates.
 * Supports multiple channels (email, LinkedIn) with copy-to-clipboard functionality.
 * Highlights personalization elements.
 * 
 * Reference: 00_frontend_specification.md - Results Visualization
 * Reference: 08_agent_specifications.md - Outreach Agent
 */

interface OutreachMessage {
  id: string;
  candidateName: string;
  channel: 'email' | 'linkedin' | 'sms';
  subject?: string; // For email
  message: string;
  personalizationHighlights: string[]; // Key personalized elements
  tone: 'professional' | 'casual' | 'enthusiastic';
  generatedAt: string;
}

interface OutreachPreviewProps {
  messages: OutreachMessage[];
  className?: string;
}

export function OutreachPreview({ messages, className = '' }: OutreachPreviewProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedChannel, setSelectedChannel] = useState<'all' | 'email' | 'linkedin' | 'sms'>('all');

  // Filter messages by channel
  const filteredMessages = selectedChannel === 'all'
    ? messages
    : messages.filter(msg => msg.channel === selectedChannel);

  // Copy message to clipboard
  const handleCopy = async (message: OutreachMessage) => {
    const textToCopy = message.subject
      ? `Subject: ${message.subject}\n\n${message.message}`
      : message.message;

    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopiedId(message.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Get channel icon
  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email':
        return <Mail className="h-4 w-4" />;
      case 'linkedin':
        return <Linkedin className="h-4 w-4" />;
      case 'sms':
        return <MessageSquare className="h-4 w-4" />;
      default:
        return <Mail className="h-4 w-4" />;
    }
  };

  // Get channel color
  const getChannelColor = (channel: string) => {
    switch (channel) {
      case 'email':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
      case 'linkedin':
        return 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300';
      case 'sms':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Outreach Messages</CardTitle>
        <CardDescription>
          AI-generated personalized messages for top candidates
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Channel Filter */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <Button
            variant={selectedChannel === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedChannel('all')}
          >
            All ({messages.length})
          </Button>
          <Button
            variant={selectedChannel === 'email' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedChannel('email')}
          >
            <Mail className="h-4 w-4 mr-1" />
            Email ({messages.filter(m => m.channel === 'email').length})
          </Button>
          <Button
            variant={selectedChannel === 'linkedin' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedChannel('linkedin')}
          >
            <Linkedin className="h-4 w-4 mr-1" />
            LinkedIn ({messages.filter(m => m.channel === 'linkedin').length})
          </Button>
          <Button
            variant={selectedChannel === 'sms' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedChannel('sms')}
          >
            <MessageSquare className="h-4 w-4 mr-1" />
            SMS ({messages.filter(m => m.channel === 'sms').length})
          </Button>
        </div>

        {/* Messages List */}
        <div className="space-y-4">
          {filteredMessages.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No messages for selected channel
            </div>
          ) : (
            filteredMessages.map((message) => (
              <div
                key={message.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                {/* Message Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        {message.candidateName}
                      </h4>
                      <Badge className={getChannelColor(message.channel)}>
                        <span className="flex items-center gap-1">
                          {getChannelIcon(message.channel)}
                          {message.channel}
                        </span>
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {message.tone}
                      </Badge>
                    </div>
                    {message.subject && (
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Subject: {message.subject}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopy(message)}
                    className="ml-2"
                  >
                    {copiedId === message.id ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                {/* Message Content */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded p-3 mb-3">
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {message.message}
                  </p>
                </div>

                {/* Personalization Highlights */}
                {message.personalizationHighlights.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                      Personalization Elements:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.personalizationHighlights.map((highlight, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="text-xs bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300"
                        >
                          {highlight}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Summary Stats */}
        {messages.length > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {messages.length}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Total Messages</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {new Set(messages.map(m => m.candidateName)).size}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Candidates</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {new Set(messages.map(m => m.channel)).size}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Channels</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
