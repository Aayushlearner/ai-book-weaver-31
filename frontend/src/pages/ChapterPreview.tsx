import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBookStore } from '@/store/bookStore';
import { MaterialButton } from '@/components/MaterialButton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, FileDown, Edit } from 'lucide-react';
import { toast } from 'sonner';

export default function ChapterPreview() {
  const navigate = useNavigate();
  const { generatedChapters } = useBookStore();
  const [activeChapter, setActiveChapter] = useState(0);

  if (generatedChapters.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-foreground">No chapters generated yet</h2>
          <MaterialButton onClick={() => navigate('/create')}>
            Create a Book
          </MaterialButton>
        </div>
      </div>
    );
  }

  const handleCopyContent = () => {
    const content = generatedChapters[activeChapter].content || '';
    navigator.clipboard.writeText(content);
    toast.success('Content copied to clipboard!');
  };

  const formatChapterContent = (raw: string): string => {
    if (!raw) return '';

    // If the content already contains HTML headings, use as-is
    if (raw.includes('<h2') || raw.includes('<h3') || raw.includes('<h2') || raw.includes('<h3')) {
      return raw;
    }

    let text = raw.trim();

    // Convert markdown-style bold headings (**Heading**) to plain text
    text = text.replace(/\*\*(.+?)\*\*/g, '$1');

    const lines = text.split(/\r?\n/);
    const result: string[] = [];
    let firstHeadingDone = false;

    for (const rawLine of lines) {
      const line = rawLine.trimEnd();
      const trimmed = line.trim();

      if (!firstHeadingDone && trimmed.length > 0) {
        // Treat the first non-empty line as the main section heading
        result.push(`<h2>${trimmed}</h2>`);
        firstHeadingDone = true;
        continue;
      }

      // Treat numbered section lines like "1.1 Defining Enterprise AI" as subheadings
      if (/^\d+(\.\d+)+\s+.+/.test(trimmed)) {
        result.push(`<h3>${trimmed}</h3>`);
        continue;
      }

      // Treat lines that look like headings (short, no punctuation at end, title case) as subheadings
      // This catches "Key Concepts", "Machine Learning", etc.
      if (trimmed.length > 0 && trimmed.length < 80 && !/[.!?]$/.test(trimmed) && /^[A-Z]/.test(trimmed) && !trimmed.includes('  ')) {
         // Simple heuristic: if it's short, starts with capital, doesn't end in punctuation, treat as heading
         // Also check it's not just a short sentence (heuristic)
         result.push(`<h3>${trimmed}</h3>`);
         continue;
      }

      result.push(line);
    }

    return result.join('\n');
  };

  return (
    <div className="min-h-screen py-12 bg-gradient-to-br from-background to-primary/5">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Chapter Preview</h1>
            <p className="text-lg text-muted-foreground">
              Review and edit your generated content
            </p>
          </div>
          <div className="flex gap-3">
            <MaterialButton variant="outline" onClick={handleCopyContent}>
              <Copy className="h-4 w-4" />
              Copy
            </MaterialButton>
            <MaterialButton variant="accent" onClick={() => navigate('/export')}>
              <FileDown className="h-4 w-4" />
              Export Book
            </MaterialButton>
          </div>
        </div>

        <div className="rounded-2xl bg-card material-shadow-xl overflow-hidden">
          <Tabs value={activeChapter.toString()} onValueChange={(v) => setActiveChapter(Number(v))}>
            <div className="border-b border-border bg-secondary/30 p-2 overflow-x-auto">
              <TabsList className="inline-flex gap-2">
                {generatedChapters.map((chapter, index) => (
                  <TabsTrigger
                    key={chapter.id}
                    value={index.toString()}
                    className="px-4 py-2 rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground material-shadow-sm transition-smooth"
                  >
                    Chapter {index + 1}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>

            {generatedChapters.map((chapter, index) => (
              <TabsContent key={chapter.id} value={index.toString()} className="p-0">
                <div className="p-8 md:p-12">
                  <div className="prose prose-lg max-w-none">
                    <div className="mb-8">
                      <h2 className="text-3xl font-bold text-foreground mb-4">
                        {chapter.title}
                      </h2>
                      <div className="h-1 w-24 gradient-accent rounded-full" />
                    </div>
                    
                    <div
                      className="text-foreground leading-relaxed prose-headings:text-primary prose-headings:font-extrabold prose-h1:text-4xl prose-h1:font-bold prose-h1:mt-8 prose-h1:mb-4 prose-h2:text-4xl md:prose-h2:text-5xl prose-h2:mt-8 prose-h2:mb-4 prose-h2:border-b-2 prose-h2:border-primary/30 prose-h2:pb-2 prose-h3:text-3xl md:prose-h3:text-4xl prose-h3:mt-6 prose-h3:mb-4 prose-h3:text-primary prose-h3:font-bold prose-h3:tracking-wide prose-h3:border-l-4 prose-h3:border-primary prose-h3:pl-4 prose-h3:bg-primary/5 prose-h3:py-2 prose-h3:rounded-r-lg prose-p:mb-4 prose-p:text-base prose-p:text-muted-foreground prose-ul:mb-4 prose-li:mb-2"
                      dangerouslySetInnerHTML={{ __html: formatChapterContent(chapter.content || '') }}
                    />
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </div>
    </div>
  );
}
