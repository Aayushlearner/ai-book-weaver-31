import { useBookStore } from '@/store/bookStore';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';

export const LoadingModal = () => {
  const { isLoading, loadingMessage } = useBookStore();

  return (
    <Dialog open={isLoading}>
      <DialogContent className="sm:max-w-md">
        <div className="flex flex-col items-center justify-center space-y-6 py-8">
          <div className="relative">
            <div className="absolute inset-0 animate-pulse rounded-full bg-primary/20 blur-xl" />
            <Loader2 className="relative h-16 w-16 animate-spin text-primary" />
          </div>
          
          <div className="space-y-3 text-center">
            <h3 className="text-xl font-semibold text-foreground">
              {loadingMessage || 'Processing...'}
            </h3>
            <Progress value={undefined} className="w-64" />
            <p className="text-sm text-muted-foreground">
              This may take a few moments
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
