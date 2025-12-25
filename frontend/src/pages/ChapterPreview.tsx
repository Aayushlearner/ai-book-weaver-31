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

  const formatChapterContent = (raw: string, chapterTitle?: string): string => {
    if (!raw) return '';

    const escapeHtml = (value: string) =>
      value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');

    const hasHtmlHeadings = /<h[1-6][\s>]/i.test(raw);

    // Many model outputs are mixed HTML: headings exist, but body text may be outside <p> tags.
    // Try a DOM-based normalization first for best accuracy. If it fails, use the regex-based fallback below.
    if (hasHtmlHeadings) {
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(raw, 'text/html');

        // Remove duplicate title at the very top of content (e.g., <h1>, <p><strong>Title</strong>)
        const norm = (s: string) => s.replace(/\s+/g, ' ').trim().toLowerCase();
        const titleCandidates: string[] = chapterTitle
          ? [chapterTitle, chapterTitle.replace(/^chapter\s*\d+\s*:\s*/i, '')]
          : [];
        const candidateSet = new Set(titleCandidates.map(norm));
        // Remove leading elements matching the chapter title
        while (doc.body.firstElementChild) {
          const first = doc.body.firstElementChild as HTMLElement;
          const text = norm(first.textContent || '');
          if (candidateSet.has(text)) {
            doc.body.removeChild(first);
            continue;
          }
          break;
        }
        // Remove an <h1> matching the title anywhere (wrapper already shows the title)
        if (chapterTitle) {
          doc.body.querySelectorAll('h1').forEach((el) => {
            if (candidateSet.has(norm(el.textContent || ''))) el.remove();
          });
        }

        // Apply spacing/styles to existing blocks (compact paragraphs, emphasized subheadings)
        doc.body.querySelectorAll('h2').forEach((el) => el.setAttribute('style', 'margin-top:24px;margin-bottom:10px;font-size:1.5rem;font-weight:800;border-bottom:1px solid rgba(59,130,246,0.25);padding-bottom:6px;'));
        doc.body.querySelectorAll('h3').forEach((el) => el.setAttribute('style', 'margin-top:18px;margin-bottom:8px;font-size:1.25rem;font-weight:700;border-bottom:1px solid rgba(59,130,246,0.2);padding-bottom:4px;'));
        doc.body.querySelectorAll('p').forEach((el) => el.setAttribute('style', 'margin:8px 0;line-height:1.7;'));
        doc.body.querySelectorAll('ul').forEach((el) => el.setAttribute('style', 'margin:12px 0;padding-left:1.25rem;list-style:disc;'));
        doc.body.querySelectorAll('br').forEach((br) => br.replaceWith(doc.createTextNode('\n')));

        const blockTags = new Set(['P','LI','H1','H2','H3','H4','H5','H6','UL','OL','TABLE','SECTION','ARTICLE','DIV']);
        const wrapLooseContent = (root: Element) => {
          const nodes = Array.from(root.childNodes);
          for (const node of nodes) {
            if (node.nodeType === Node.TEXT_NODE) {
              const text = (node.textContent || '').replace(/\s+/g, ' ').trim();
              if (text) {
                // Split into sentences and group them 2 per paragraph
                const sentences = text.match(/[^.!?]+[.!?]+(?=\s|$)/g) || [text];
                for (let i = 0; i < sentences.length; i += 2) {
                  const chunk = sentences.slice(i, i + 2).join(' ').trim();
                  if (chunk) {
                    const p = doc.createElement('p');
                    p.setAttribute('style', 'margin:8px 0;line-height:1.7;');
                    p.textContent = chunk;
                    root.insertBefore(p, node);
                  }
                }
              }
              root.removeChild(node);
            } else if (node.nodeType === Node.ELEMENT_NODE) {
              const el = node as HTMLElement;
              if (blockTags.has(el.tagName)) {
                wrapLooseContent(el);
              } else {
                // Inline element at block level: wrap it into a paragraph
                const p = doc.createElement('p');
                p.setAttribute('style', 'margin:8px 0;line-height:1.7;');
                root.insertBefore(p, el);
                p.appendChild(el);
              }
            }
          }
        };

        wrapLooseContent(doc.body);
        return doc.body.innerHTML;
      } catch (e) {
        // Fall through to regex-based normalization below
      }

      const prepared = raw
        .replace(/\r\n/g, '\n')
        .replace(/<\s*br\s*\/?>/gi, '\n')
        // Enforce spacing via inline styles on existing tags
        .replace(/<\s*h2\b[^>]*>/gi, '<h2 style="margin-top: 24px; margin-bottom: 10px; font-size: 1.5rem; font-weight: 800; border-bottom: 1px solid rgba(59,130,246,0.25); padding-bottom: 6px;">')
        .replace(/<\s*h3\b[^>]*>/gi, '<h3 style="margin-top: 18px; margin-bottom: 8px; font-size: 1.25rem; font-weight: 700; border-bottom: 1px solid rgba(59,130,246,0.2); padding-bottom: 4px;">')
        .replace(/<\s*p\b[^>]*>/gi, '<p style="margin: 8px 0; line-height: 1.7;">')
        .replace(/<\s*ul\b[^>]*>/gi, '<ul style="margin: 12px 0; padding-left: 1.25rem; list-style: disc;">')
        // Put headings and common block tags on their own lines
        .replace(/<\s*(h[1-6][^>]*)>/gi, '\n<$1>')
        .replace(/<\s*\/(h[1-6])\s*>/gi, '</$1>\n')
        .replace(/<\s*(p[^>]*)>/gi, '\n<$1>')
        .replace(/<\s*\/(p)\s*>/gi, '</$1>\n')
        .replace(/<\s*(ul[^>]*)>/gi, '\n<$1>')
        .replace(/<\s*\/(ul)\s*>/gi, '</$1>\n')
        .replace(/<\s*(li[^>]*)>/gi, '\n<$1>')
        .replace(/<\s*\/(li)\s*>/gi, '</$1>\n');

      const lines = prepared.split(/\n/);
      const out: string[] = [];

      let inList = false;

      const closeList = () => {
        if (inList) {
          out.push('</ul>');
          inList = false;
        }
      };

      for (const rawLine of lines) {
        const trimmed = rawLine.trim();

        if (!trimmed) {
          closeList();
          continue;
        }

        // Keep existing HTML tags as-is (block boundaries). We now keep <p> as well (styled above).
        if (/^<\/?(h[1-6]|ul|li|p)\b/i.test(trimmed)) {
          // If a new section starts, close any open list to avoid nesting issues
          if (/^<h[1-6]\b/i.test(trimmed) || /^<\/h[1-6]>/i.test(trimmed)) {
            closeList();
          }
          out.push(trimmed);
          continue;
        }

        // Convert plain-text bullets into HTML list items
        const bulletMatch = /^[-*]\s+(.+)$/.exec(trimmed);
        if (bulletMatch) {
          if (!inList) {
            out.push('<ul style="margin: 12px 0; padding-left: 1.25rem; list-style: disc;">');
            inList = true;
          }
          out.push(`<li>${escapeHtml(bulletMatch[1].trim())}</li>`);
          continue;
        }

        // Otherwise render this text as paragraphs. If it's very long, split by sentences (2 per paragraph)
        closeList();
        const sentences = trimmed.match(/[^.!?]+[.!?]+(?=\s|$)/g) || [trimmed];
        if (sentences.length <= 1) {
          out.push(`<p style=\"margin: 8px 0; line-height: 1.7;\">${escapeHtml(trimmed)}</p>`);
        } else {
          const para: string[] = [];
          for (let i = 0; i < sentences.length; i += 2) {
            const chunk = sentences.slice(i, i + 2).join(' ').trim();
            if (chunk.length > 0) {
              out.push(`<p style=\"margin: 8px 0; line-height: 1.7;\">${escapeHtml(chunk)}</p>`);
            }
          }
        }
      }

      closeList();

      // Strip duplicate title if present at the top of the HTML we just built
      const built = out.join('\n');
      const stripDup = (html: string, t?: string) => {
        if (!t) return html;
        try {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const norm = (s: string) => s.replace(/\s+/g, ' ').trim().toLowerCase();
          const candidates = [t, t.replace(/^chapter\s*\d+\s*:\s*/i, '')].map((x) => norm(x));
          while (doc.body.firstElementChild) {
            const first = doc.body.firstElementChild as HTMLElement;
            if (candidates.includes(norm(first.textContent || ''))) {
              doc.body.removeChild(first);
              continue;
            }
            break;
          }
          return doc.body.innerHTML;
        } catch {
          return html;
        }
      };
      return stripDup(built, chapterTitle);
    }

    let text = raw.trim();

    // Convert markdown-style bold headings (**Heading**) to plain text
    text = text.replace(/\*\*(.+?)\*\*/g, '$1');

    const lines = text.split(/\r?\n/);
    const result: string[] = [];
    let firstHeadingDone = false;

    let inList = false;
    const closeListIfOpen = () => {
      if (inList) {
        result.push(`</ul>`);
        inList = false;
      }
    };

    for (const rawLine of lines) {
      const line = rawLine.trimEnd();
      const trimmed = line.trim();

      // Blank line: close lists and add spacing
      if (trimmed.length === 0) {
        closeListIfOpen();
        continue;
      }

      const safe = escapeHtml(trimmed);

      if (!firstHeadingDone && trimmed.length > 0) {
        // Treat the first non-empty line as the main section heading
        result.push(`<h2 style=\"margin-top: 24px; margin-bottom: 10px; font-size: 1.5rem; font-weight: 800; border-bottom: 1px solid rgba(59,130,246,0.25); padding-bottom: 6px;\">${safe}</h2>`);
        firstHeadingDone = true;
        continue;
      }

      // Treat numbered section lines like "1.1 Defining Enterprise AI" as subheadings
      if (/^\d+(\.\d+)+\s+.+/.test(trimmed)) {
        closeListIfOpen();
        result.push(`<h3 style=\"margin-top: 18px; margin-bottom: 8px; font-size: 1.25rem; font-weight: 700; border-bottom: 1px solid rgba(59,130,246,0.2); padding-bottom: 4px;\">${safe}</h3>`);
        continue;
      }

      // Bullet lines: "- item" or "* item"
      const bulletMatch = /^[-*]\s+(.+)$/.exec(trimmed);
      if (bulletMatch) {
        if (!inList) {
          result.push('<ul>');
          inList = true;
        }
        result.push(`<li>${escapeHtml(bulletMatch[1].trim())}</li>`);
        continue;
      }

      // Treat lines that look like headings (short, no punctuation at end, title case) as subheadings
      // This catches "Key Concepts", "Machine Learning", etc.
      if (trimmed.length > 0 && trimmed.length < 80 && !/[.!?]$/.test(trimmed) && /^[A-Z]/.test(trimmed) && !trimmed.includes('  ')) {
         // Simple heuristic: if it's short, starts with capital, doesn't end in punctuation, treat as heading
         // Also check it's not just a short sentence (heuristic)
         closeListIfOpen();
         result.push(`<h3 style=\"margin-top: 18px; margin-bottom: 8px; font-size: 1.25rem; font-weight: 700; border-bottom: 1px solid rgba(59,130,246,0.2); padding-bottom: 4px;\">${safe}</h3>`);
         continue;
      }

      closeListIfOpen();
      result.push(`<p style=\"margin: 8px 0; line-height: 1.7;\">${safe}</p>`);
    }

    closeListIfOpen();

    const built = result.join('\n');
    const stripDup = (html: string, t?: string) => {
      if (!t) return html;
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const norm = (s: string) => s.replace(/\s+/g, ' ').trim().toLowerCase();
        const candidates = [t, t.replace(/^chapter\s*\d+\s*:\s*/i, '')].map((x) => norm(x));
        while (doc.body.firstElementChild) {
          const first = doc.body.firstElementChild as HTMLElement;
          if (candidates.includes(norm(first.textContent || ''))) {
            doc.body.removeChild(first);
            continue;
          }
          break;
        }
        return doc.body.innerHTML;
      } catch {
        return html;
      }
    };
    return stripDup(built, chapterTitle);
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

        <div className="rounded-2xl glass glass-border material-shadow-xl overflow-hidden">
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
                  <div className="max-w-none">
                    <div className="mb-8">
                      <h2 className="text-3xl font-bold text-foreground mb-4">
                        {chapter.title}
                      </h2>
                      <div className="h-1 w-24 gradient-accent rounded-full" />
                    </div>
                    
                    <div
                      className="prose prose-lg max-w-none text-foreground leading-relaxed prose-headings:text-primary prose-h1:hidden prose-p:my-2 prose-p:text-base prose-p:leading-7 prose-ul:my-3 prose-ul:pl-6 prose-li:my-1"
                      dangerouslySetInnerHTML={{ __html: formatChapterContent(chapter.content || '', chapter.title) }}
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
