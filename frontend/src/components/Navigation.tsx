import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { BookOpen, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { DarkModeToggle } from '@/components/ui/dark-mode-toggle';

export const Navigation = () => {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { to: '/', label: 'Home' },
    { to: '/create', label: 'Create Book' },
    { to: '/workspace', label: 'TOC Workspace' },
    { to: '/preview', label: 'Preview' },
    { to: '/export', label: 'Export' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-lg material-shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="rounded-lg bg-gradient-primary p-2 material-shadow-md group-hover:material-shadow-lg transition-smooth">
              <BookOpen className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              AI BookGen
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-smooth relative',
                  isActive(link.to)
                    ? 'text-primary bg-primary/10'
                    : 'text-foreground/70 hover:text-foreground hover:bg-secondary/50'
                )}
              >
                {link.label}
                {isActive(link.to) && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-8 bg-primary rounded-full" />
                )}
              </Link>
            ))}
          </div>

          {/* Theme Toggle and Mobile Menu */}
          <div className="flex items-center gap-2">
            <DarkModeToggle />
            <button
              className="md:hidden p-2 rounded-lg hover:bg-secondary transition-smooth"
              onClick={() => setIsOpen(!isOpen)}
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden py-4 space-y-2 border-t border-border">
            {links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setIsOpen(false)}
                className={cn(
                  'block px-4 py-2 rounded-lg text-sm font-medium transition-smooth',
                  isActive(link.to)
                    ? 'text-primary bg-primary/10'
                    : 'text-foreground/70 hover:text-foreground hover:bg-secondary/50'
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
};
