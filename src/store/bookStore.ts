import { create } from 'zustand';

export interface Chapter {
  id: string;
  title: string;
  content?: string;
  subtopics?: Chapter[];
  isExpanded?: boolean;
}

export interface BookFormData {
  topic: string;
  numberOfChapters: number;
  tone: 'formal' | 'casual' | 'academic' | 'storytelling';
  includeSummaries: boolean;
  includeImages: boolean;
  includeVoiceNarration: boolean;
  userToc?: File;
}

interface BookStore {
  formData: BookFormData;
  aiGeneratedToc: Chapter[];
  userCreatedToc: Chapter[];
  mergedToc: Chapter[];
  generatedChapters: Chapter[];
  isLoading: boolean;
  loadingMessage: string;
  
  setFormData: (data: Partial<BookFormData>) => void;
  setAiGeneratedToc: (toc: Chapter[]) => void;
  setUserCreatedToc: (toc: Chapter[]) => void;
  setMergedToc: (toc: Chapter[]) => void;
  setGeneratedChapters: (chapters: Chapter[]) => void;
  setLoading: (loading: boolean, message?: string) => void;
  resetStore: () => void;
}

const initialFormData: BookFormData = {
  topic: '',
  numberOfChapters: 5,
  tone: 'formal',
  includeSummaries: false,
  includeImages: false,
  includeVoiceNarration: false,
};

export const useBookStore = create<BookStore>((set) => ({
  formData: initialFormData,
  aiGeneratedToc: [],
  userCreatedToc: [],
  mergedToc: [],
  generatedChapters: [],
  isLoading: false,
  loadingMessage: '',

  setFormData: (data) =>
    set((state) => ({ formData: { ...state.formData, ...data } })),

  setAiGeneratedToc: (toc) => set({ aiGeneratedToc: toc }),

  setUserCreatedToc: (toc) => set({ userCreatedToc: toc }),

  setMergedToc: (toc) => set({ mergedToc: toc }),

  setGeneratedChapters: (chapters) => set({ generatedChapters: chapters }),

  setLoading: (loading, message = '') =>
    set({ isLoading: loading, loadingMessage: message }),

  resetStore: () =>
    set({
      formData: initialFormData,
      aiGeneratedToc: [],
      userCreatedToc: [],
      mergedToc: [],
      generatedChapters: [],
      isLoading: false,
      loadingMessage: '',
    }),
}));
