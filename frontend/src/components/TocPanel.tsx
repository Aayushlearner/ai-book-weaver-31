import { useState } from 'react';
import { Chapter } from '@/store/bookStore';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, ChevronDown, ChevronRight, Edit2, Trash2, Plus } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { MaterialButton } from '@/components/MaterialButton';

interface TocPanelProps {
  title: string;
  chapters: Chapter[];
  onChaptersChange: (chapters: Chapter[]) => void;
  editable?: boolean;
}

interface SortableChapterProps {
  chapter: Chapter;
  onToggle: () => void;
  onEdit: (id: string, title: string) => void;
  onDelete: (id: string) => void;
  onAddSubtopic: (chapterId: string) => void;
}

function SortableChapter({ chapter, onToggle, onEdit, onDelete, onAddSubtopic }: SortableChapterProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(chapter.title);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: chapter.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleSave = () => {
    if (editValue.trim()) {
      onEdit(chapter.id, editValue.trim());
      setIsEditing(false);
    }
  };

  return (
    <div ref={setNodeRef} style={style} className="space-y-2">
      <div className="group flex items-center gap-2 p-3 rounded-lg bg-background border border-border hover:border-primary/50 transition-smooth material-shadow-sm">
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground transition-colors"
        >
          <GripVertical className="h-4 w-4" />
        </button>

        <button onClick={onToggle} className="text-muted-foreground hover:text-foreground transition-colors">
          {chapter.isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>

        {isEditing ? (
          <Input
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleSave}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            className="h-8 flex-1"
            autoFocus
          />
        ) : (
          <span className="flex-1 font-medium text-lg text-foreground">{chapter.title}</span>
        )}

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => setIsEditing(true)}
            className="p-1.5 rounded hover:bg-secondary transition-colors"
          >
            <Edit2 className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          <button
            onClick={() => onAddSubtopic(chapter.id)}
            className="p-1.5 rounded hover:bg-secondary transition-colors"
          >
            <Plus className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          <button
            onClick={() => onDelete(chapter.id)}
            className="p-1.5 rounded hover:bg-destructive/10 transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5 text-destructive" />
          </button>
        </div>
      </div>

      {chapter.isExpanded && chapter.subtopics && chapter.subtopics.length > 0 && (
        <div className="ml-8 space-y-2">
          {chapter.subtopics.map((subtopic) => (
            <div
              key={subtopic.id}
              className="flex items-center gap-2 p-2 rounded-lg bg-secondary/50 border border-border text-sm"
            >
              <span className="flex-1 text-foreground">{subtopic.title}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TocPanel({ title, chapters, onChaptersChange, editable = true }: TocPanelProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = chapters.findIndex((ch) => ch.id === active.id);
      const newIndex = chapters.findIndex((ch) => ch.id === over.id);
      onChaptersChange(arrayMove(chapters, oldIndex, newIndex));
    }
  };

  const handleToggle = (id: string) => {
    onChaptersChange(
      chapters.map((ch) =>
        ch.id === id ? { ...ch, isExpanded: !ch.isExpanded } : ch
      )
    );
  };

  const handleEdit = (id: string, title: string) => {
    onChaptersChange(
      chapters.map((ch) => (ch.id === id ? { ...ch, title } : ch))
    );
  };

  const handleDelete = (id: string) => {
    onChaptersChange(chapters.filter((ch) => ch.id !== id));
  };

  const handleAddSubtopic = (chapterId: string) => {
    onChaptersChange(
      chapters.map((ch) =>
        ch.id === chapterId
          ? {
              ...ch,
              subtopics: [
                ...(ch.subtopics || []),
                { id: `${chapterId}-sub-${Date.now()}`, title: 'New Subtopic' },
              ],
            }
          : ch
      )
    );
  };

  const handleAddChapter = () => {
    const newChapter: Chapter = {
      id: `chapter-${Date.now()}`,
      title: 'New Chapter',
      subtopics: [],
      isExpanded: false,
    };
    onChaptersChange([...chapters, newChapter]);
  };

  return (
    <div className="h-full flex flex-col rounded-2xl bg-card material-shadow-lg border border-border overflow-hidden">
      <div className="p-6 border-b border-border bg-gradient-to-r from-primary/5 to-accent/5">
        <h3 className="text-xl font-bold text-foreground">{title}</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-3">
        {chapters.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No chapters yet</p>
          </div>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={chapters.map((ch) => ch.id)} strategy={verticalListSortingStrategy}>
              {chapters.map((chapter) => (
                <SortableChapter
                  key={chapter.id}
                  chapter={chapter}
                  onToggle={() => handleToggle(chapter.id)}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onAddSubtopic={handleAddSubtopic}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>

      {editable && (
        <div className="p-4 border-t border-border bg-secondary/30">
          <MaterialButton variant="outline" size="sm" className="w-full" onClick={handleAddChapter}>
            <Plus className="h-4 w-4" />
            Add Chapter
          </MaterialButton>
        </div>
      )}
    </div>
  );
}
