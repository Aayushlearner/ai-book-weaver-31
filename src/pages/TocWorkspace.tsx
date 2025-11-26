import { useNavigate } from 'react-router-dom';
import { useBookStore } from '@/store/bookStore';
import { TocPanel } from '@/components/TocPanel';
import { MaterialButton } from '@/components/MaterialButton';
import { writeBook } from '@/lib/api';
import { ArrowRight, Combine } from 'lucide-react';
import { toast } from 'sonner';

export default function TocWorkspace() {
  const navigate = useNavigate();
  const {
    aiGeneratedToc,
    userCreatedToc,
    setAiGeneratedToc,
    setUserCreatedToc,
    setMergedToc,
    setGeneratedChapters,
    setLoading,
    formData,
  } = useBookStore();

  const handleMergeAndContinue = async () => {
    const merged = [...aiGeneratedToc, ...userCreatedToc];
    
    if (merged.length === 0) {
      toast.error('Please create or generate at least one chapter');
      return;
    }

    setMergedToc(merged);
    setLoading(true, 'Writing your book...');

    try {
      const chapters = await writeBook(merged, formData);
      setGeneratedChapters(chapters);
      toast.success('Book generated successfully!');
      navigate('/preview');
    } catch (error) {
      toast.error('Failed to generate book. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-12 bg-gradient-to-br from-background to-primary/5">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-4 mb-8">
          <h1 className="text-4xl font-bold text-foreground">TOC Workspace</h1>
          <p className="text-lg text-muted-foreground">
            Organize and customize your book's structure
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <TocPanel
            title="AI Generated TOC"
            chapters={aiGeneratedToc}
            onChaptersChange={setAiGeneratedToc}
          />
          <TocPanel
            title="User Created TOC"
            chapters={userCreatedToc}
            onChaptersChange={setUserCreatedToc}
          />
        </div>

        <div className="flex justify-center">
          <MaterialButton variant="accent" size="lg" onClick={handleMergeAndContinue}>
            <Combine className="h-5 w-5" />
            Merge & Continue
            <ArrowRight className="h-5 w-5" />
          </MaterialButton>
        </div>
      </div>
    </div>
  );
}
