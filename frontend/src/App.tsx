import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/lib/theme-provider";
import { Navigation } from "@/components/Navigation";
import { LoadingModal } from "@/components/LoadingModal";
import Landing from "./pages/Landing";
import BookCreation from "./pages/BookCreation";
import TocWorkspace from "./pages/TocWorkspace";
import ChapterPreview from "./pages/ChapterPreview";
import Export from "./pages/Export";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider defaultTheme="light" storageKey="ai-book-weaver-theme">
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <LoadingModal />
        <BrowserRouter>
          <div className="min-h-screen bg-background relative">
            <div className="ui-mirror-bg" />
            <Navigation />
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/create" element={<BookCreation />} />
              <Route path="/workspace" element={<TocWorkspace />} />
              <Route path="/preview" element={<ChapterPreview />} />
              <Route path="/export" element={<Export />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
