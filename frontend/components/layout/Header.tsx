import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { useWorkflowStore } from '@/store/workflowStore';

export function Header() {
  const demoMode = useWorkflowStore((state) => state.demoMode);
  const toggleDemoMode = useWorkflowStore((state) => state.toggleDemoMode);
  
  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">T</span>
            </div>
            <span className="font-bold text-xl">Talent Accelerator</span>
          </Link>
          
          <nav className="flex items-center space-x-6">
            <Link 
              href="/" 
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              New Job
            </Link>
            
            <button
              onClick={toggleDemoMode}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              {demoMode ? (
                <Badge variant="secondary">Demo Mode ON</Badge>
              ) : (
                <span>Demo Mode</span>
              )}
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
