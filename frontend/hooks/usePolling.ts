import { useEffect, useRef, useCallback } from 'react';

interface UsePollingOptions {
  interval?: number;
  enabled?: boolean;
  onError?: (error: Error) => void;
}

/**
 * Generic polling hook for periodic data fetching
 * 
 * @param callback - Function to call on each poll
 * @param options - Polling configuration
 */
export const usePolling = (
  callback: () => Promise<void> | void,
  options: UsePollingOptions = {}
) => {
  const {
    interval = 2000,
    enabled = true,
    onError,
  } = options;
  
  const savedCallback = useRef(callback);
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  // Update callback ref when it changes
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);
  
  const poll = useCallback(async () => {
    try {
      await savedCallback.current();
    } catch (error) {
      console.error('Polling error:', error);
      if (onError && error instanceof Error) {
        onError(error);
      }
    }
  }, [onError]);
  
  useEffect(() => {
    if (!enabled) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      return;
    }
    
    const tick = async () => {
      await poll();
      timeoutRef.current = setTimeout(tick, interval);
    };
    
    // Start polling
    tick();
    
    // Cleanup
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, interval, poll]);
};

/**
 * Hook for conditional polling based on a condition
 */
export const useConditionalPolling = (
  callback: () => Promise<boolean> | boolean,
  options: UsePollingOptions = {}
) => {
  const {
    interval = 2000,
    enabled = true,
    onError,
  } = options;
  
  const savedCallback = useRef(callback);
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);
  
  const poll = useCallback(async () => {
    try {
      const shouldContinue = await savedCallback.current();
      return shouldContinue;
    } catch (error) {
      console.error('Conditional polling error:', error);
      if (onError && error instanceof Error) {
        onError(error);
      }
      return false;
    }
  }, [onError]);
  
  useEffect(() => {
    if (!enabled) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      return;
    }
    
    const tick = async () => {
      const shouldContinue = await poll();
      if (shouldContinue) {
        timeoutRef.current = setTimeout(tick, interval);
      }
    };
    
    tick();
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, interval, poll]);
};
