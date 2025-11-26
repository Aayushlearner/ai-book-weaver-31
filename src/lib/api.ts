import { BookFormData, Chapter } from '@/store/bookStore';

// Placeholder API functions for backend endpoints

export const generateToc = async (formData: BookFormData): Promise<Chapter[]> => {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 2000));
  
  // Mock response
  const mockToc: Chapter[] = Array.from({ length: formData.numberOfChapters }, (_, i) => ({
    id: `ai-chapter-${i + 1}`,
    title: `Chapter ${i + 1}: ${formData.topic} - Part ${i + 1}`,
    subtopics: [
      { id: `ai-chapter-${i + 1}-sub-1`, title: 'Introduction' },
      { id: `ai-chapter-${i + 1}-sub-2`, title: 'Main Concepts' },
      { id: `ai-chapter-${i + 1}-sub-3`, title: 'Practical Applications' },
    ],
    isExpanded: false,
  }));

  return mockToc;
};

export const saveUserToc = async (toc: Chapter[]): Promise<void> => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 1000));
  console.log('User TOC saved:', toc);
};

export const writeBook = async (
  mergedToc: Chapter[],
  formData: BookFormData
): Promise<Chapter[]> => {
  // Simulate book generation delay
  await new Promise((resolve) => setTimeout(resolve, 3000));

  // Mock generated chapters with content
  const generatedChapters: Chapter[] = mergedToc.map((chapter) => ({
    ...chapter,
    content: `
# ${chapter.title}

This is the generated content for **${chapter.title}** written in a ${formData.tone} tone.

## Overview

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

${chapter.subtopics?.map((sub) => `
### ${sub.title}

Detailed explanation of ${sub.title}. Proin gravida dolor sit amet lacus accumsan et viverra justo commodo. Proin sodales pulvinar tempor. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.
`).join('\n')}

## Conclusion

Vestibulum ac diam sit amet quam vehicula elementum sed sit amet dui. Curabitur arcu erat, accumsan id imperdiet et, porttitor at sem.

${formData.includeSummaries ? '\n### Summary\n\nKey takeaways from this chapter summarized for quick reference.' : ''}
    `.trim(),
    subtopics: chapter.subtopics,
  }));

  return generatedChapters;
};

export const exportBook = async (
  format: 'pdf' | 'epub' | 'markdown',
  chapters: Chapter[]
): Promise<Blob> => {
  // Simulate export delay
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Mock file generation
  const content = chapters.map((ch) => ch.content).join('\n\n---\n\n');
  const blob = new Blob([content], { type: 'text/plain' });
  
  console.log(`Exporting book as ${format}:`, chapters);
  return blob;
};
