import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBookStore } from '@/store/bookStore';
import { MaterialButton } from '@/components/MaterialButton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { generateToc } from '@/lib/api';
import { BookOpen, Upload, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export default function BookCreation() {
  const navigate = useNavigate();
  const { formData, setFormData, setAiGeneratedToc, setLoading } = useBookStore();
  const [localFormData, setLocalFormData] = useState(formData);

  const handleInputChange = (field: string, value: any) => {
    setLocalFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleInputChange('userToc', file);
      toast.success(`File "${file.name}" uploaded successfully`);
    }
  };

  const handleGenerateToc = async () => {
    if (!localFormData.topic.trim()) {
      toast.error('Please enter a book topic');
      return;
    }

    setFormData(localFormData);
    setLoading(true, 'Generating table of contents...');

    try {
      const toc = await generateToc(localFormData);
      setAiGeneratedToc(toc);
      toast.success('TOC generated successfully!');
      navigate('/workspace');
    } catch (error) {
      toast.error('Failed to generate TOC. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-12 bg-gradient-to-br from-background to-primary/5">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-4 mb-12">
          <div className="inline-flex p-4 rounded-2xl gradient-primary material-shadow-lg">
            <BookOpen className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-foreground">Create Your Book</h1>
          <p className="text-lg text-muted-foreground">
            Fill in the details below to generate your book's table of contents
          </p>
        </div>

        <div className="rounded-2xl bg-card p-8 md:p-12 material-shadow-xl space-y-8">
          {/* Topic Input */}
          <div className="space-y-2">
            <Label htmlFor="topic" className="text-base font-semibold">
              Book Topic / Title
            </Label>
            <Input
              id="topic"
              placeholder="Enter your book topic or title..."
              value={localFormData.topic}
              onChange={(e) => handleInputChange('topic', e.target.value)}
              className="h-12 text-base material-shadow-sm focus:material-shadow-md transition-smooth"
            />
          </div>

          {/* Number of Chapters */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label className="text-base font-semibold">Number of Chapters</Label>
              <span className="text-2xl font-bold text-primary">{localFormData.numberOfChapters}</span>
            </div>
            <Slider
              value={[localFormData.numberOfChapters]}
              onValueChange={(value) => handleInputChange('numberOfChapters', value[0])}
              min={3}
              max={20}
              step={1}
              className="py-4"
            />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>3 chapters</span>
              <span>20 chapters</span>
            </div>
          </div>

          {/* Tone Selection */}
          <div className="space-y-2">
            <Label htmlFor="tone" className="text-base font-semibold">
              Writing Tone
            </Label>
            <Select
              value={localFormData.tone}
              onValueChange={(value: any) => handleInputChange('tone', value)}
            >
              <SelectTrigger id="tone" className="h-12 text-base material-shadow-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="formal">Formal</SelectItem>
                <SelectItem value="casual">Casual</SelectItem>
                <SelectItem value="academic">Academic</SelectItem>
                <SelectItem value="storytelling">Storytelling</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Additional Options */}
          <div className="space-y-4 p-6 rounded-xl bg-secondary/50">
            <Label className="text-base font-semibold">Additional Options</Label>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Checkbox
                  id="summaries"
                  checked={localFormData.includeSummaries}
                  onCheckedChange={(checked) => handleInputChange('includeSummaries', checked)}
                />
                <Label htmlFor="summaries" className="text-sm cursor-pointer">
                  Include chapter summaries
                </Label>
              </div>
              <div className="flex items-center gap-3">
                <Checkbox
                  id="images"
                  checked={localFormData.includeImages}
                  onCheckedChange={(checked) => handleInputChange('includeImages', checked)}
                />
                <Label htmlFor="images" className="text-sm cursor-pointer">
                  Include images
                </Label>
              </div>
              <div className="flex items-center gap-3">
                <Checkbox
                  id="narration"
                  checked={localFormData.includeVoiceNarration}
                  onCheckedChange={(checked) => handleInputChange('includeVoiceNarration', checked)}
                />
                <Label htmlFor="narration" className="text-sm cursor-pointer">
                  Include voice narration
                </Label>
              </div>
            </div>
          </div>

          {/* File Upload */}
          <div className="space-y-2">
            <Label htmlFor="file-upload" className="text-base font-semibold">
              Upload Custom TOC (Optional)
            </Label>
            <div className="relative">
              <input
                id="file-upload"
                type="file"
                accept=".txt,.md,.doc,.docx"
                onChange={handleFileUpload}
                className="hidden"
              />
              <label htmlFor="file-upload">
                <div className="flex items-center gap-3 p-4 rounded-xl border-2 border-dashed border-border hover:border-primary transition-smooth cursor-pointer bg-secondary/30 hover:bg-secondary/50">
                  <Upload className="h-5 w-5 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {localFormData.userToc?.name || 'Click to upload or drag and drop'}
                  </span>
                </div>
              </label>
            </div>
          </div>

          {/* Generate Button */}
          <div className="pt-6">
            <MaterialButton
              variant="accent"
              size="lg"
              className="w-full"
              onClick={handleGenerateToc}
            >
              <Sparkles className="h-5 w-5" />
              Generate Table of Contents
            </MaterialButton>
          </div>
        </div>
      </div>
    </div>
  );
}
