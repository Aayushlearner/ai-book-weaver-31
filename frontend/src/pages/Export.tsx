import { useState } from 'react';
import { useBookStore } from '@/store/bookStore';
import { MaterialButton } from '@/components/MaterialButton';
import { exportBook } from '@/lib/api';
import { FileText, FileDown, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

export default function Export() {
  const { generatedChapters, setLoading } = useBookStore();
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);

  const handleExport = async (format: 'pdf' | 'epub' | 'markdown') => {
    if (generatedChapters.length === 0) {
      toast.error('No content to export. Please generate a book first.');
      return;
    }

    setExportingFormat(format);
    setLoading(true, `Exporting as ${format.toUpperCase()}...`);

    try {
      const blob = await exportBook(format, generatedChapters);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `book.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success(`Book exported successfully as ${format.toUpperCase()}!`);
    } catch (error) {
      toast.error(`Failed to export book as ${format.toUpperCase()}`);
    } finally {
      setLoading(false);
      setExportingFormat(null);
    }
  };

  const exportOptions = [
    {
      format: 'pdf' as const,
      title: 'PDF',
      description: 'Portable Document Format - Universal compatibility',
      icon: FileText,
      color: 'from-red-500 to-red-600',
    },
    {
      format: 'epub' as const,
      title: 'ePub',
      description: 'Electronic Publication - Perfect for e-readers',
      icon: BookOpen,
      color: 'from-green-500 to-green-600',
    },
    {
      format: 'markdown' as const,
      title: 'Markdown',
      description: 'Plain text format - Easy to edit and convert',
      icon: FileDown,
      color: 'from-blue-500 to-blue-600',
    },
  ];

  return (
    <div className="min-h-screen py-12 bg-gradient-to-br from-background to-primary/5">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-4 mb-12">
          <h1 className="text-4xl font-bold text-foreground">Export Your Book</h1>
          <p className="text-lg text-muted-foreground">
            Choose your preferred format to download your completed book
          </p>
        </div>

        {generatedChapters.length === 0 ? (
          <div className="text-center py-12 rounded-2xl bg-card material-shadow-lg">
            <p className="text-muted-foreground mb-4">No book content available to export</p>
            <MaterialButton onClick={() => window.location.href = '/create'}>
              Create a Book
            </MaterialButton>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {exportOptions.map((option) => {
              const Icon = option.icon;
              const isExporting = exportingFormat === option.format;
              
              return (
                <div
                  key={option.format}
                  className="group rounded-2xl bg-card border border-border material-shadow-lg hover:material-shadow-xl transition-smooth hover:-translate-y-1 overflow-hidden"
                >
                  <div className={`h-2 bg-gradient-to-r ${option.color}`} />
                  
                  <div className="p-8 space-y-6">
                    <div className="flex justify-center">
                      <div className={`inline-flex p-6 rounded-2xl bg-gradient-to-br ${option.color} material-shadow-md group-hover:material-shadow-lg transition-smooth`}>
                        <Icon className="h-12 w-12 text-white" />
                      </div>
                    </div>

                    <div className="text-center space-y-2">
                      <h3 className="text-2xl font-bold text-foreground">{option.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {option.description}
                      </p>
                    </div>

                    <MaterialButton
                      variant="primary"
                      size="lg"
                      className="w-full"
                      onClick={() => handleExport(option.format)}
                      isLoading={isExporting}
                      disabled={isExporting}
                    >
                      <FileDown className="h-5 w-5" />
                      Download {option.title}
                    </MaterialButton>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-12 p-6 rounded-2xl bg-secondary/30 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-3">Export Information</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>• All formats include complete chapter content and structure</li>
            <li>• PDF format preserves formatting and is ready to print</li>
            <li>• ePub format is optimized for e-readers and mobile devices</li>
            <li>• Markdown format allows easy editing and conversion to other formats</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
