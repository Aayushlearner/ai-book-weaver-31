import { Link } from 'react-router-dom';
import { MaterialButton } from '@/components/MaterialButton';
import { BookOpen, Wand2, FileEdit, Download, Zap, Shield, Sparkles } from 'lucide-react';

export default function Landing() {
  const features = [
    {
      icon: Wand2,
      title: 'AI-Powered Generation',
      description: 'Advanced AI creates comprehensive book structures tailored to your topic and requirements.',
    },
    {
      icon: FileEdit,
      title: 'Interactive TOC Editor',
      description: 'Drag-and-drop interface to customize and merge AI-generated and user-created content.',
    },
    {
      icon: Download,
      title: 'Multiple Export Formats',
      description: 'Export your finished book as PDF, ePub, or Markdown with a single click.',
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Generate complete book structures in seconds, not hours or days.',
    },
    {
      icon: Shield,
      title: 'Quality Content',
      description: 'Choose from multiple tones and styles to match your writing needs perfectly.',
    },
    {
      icon: Sparkles,
      title: 'Smart Features',
      description: 'Auto-generated summaries, images, and voice narration options included.',
    },
  ];

  const steps = [
    { step: '01', title: 'Enter Your Topic', description: 'Provide your book topic and preferences' },
    { step: '02', title: 'Generate TOC', description: 'AI creates a comprehensive table of contents' },
    { step: '03', title: 'Customize & Merge', description: 'Edit and organize your content structure' },
    { step: '04', title: 'Generate & Export', description: 'Create your book and download in your preferred format' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-background via-background to-primary/5 pt-20 pb-32">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 material-shadow-sm">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">AI-Powered Book Creation</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-primary via-primary-light to-accent bg-clip-text text-transparent">
                Create Books with AI
              </span>
              <br />
              <span className="text-foreground">In Minutes, Not Months</span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xl text-muted-foreground leading-relaxed">
              Transform your ideas into comprehensive, well-structured books with the power of artificial intelligence.
              Generate, customize, and export professional-quality content effortlessly.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Link to="/create">
                <MaterialButton variant="accent" size="lg">
                  <BookOpen className="h-5 w-5" />
                  Start Creating
                </MaterialButton>
              </Link>
              <MaterialButton variant="outline" size="lg">
                Learn More
              </MaterialButton>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-card">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-foreground">Powerful Features</h2>
            <p className="text-lg text-muted-foreground">Everything you need to create amazing books</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  className="group p-8 rounded-2xl bg-background border border-border material-shadow-md hover:material-shadow-xl transition-smooth hover:-translate-y-1"
                >
                  <div className="inline-flex p-3 rounded-xl bg-primary/10 text-primary material-shadow-sm group-hover:material-shadow-md transition-smooth">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-6 text-xl font-semibold text-foreground">{feature.title}</h3>
                  <p className="mt-3 text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-24 bg-background">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold text-foreground">How It Works</h2>
            <p className="text-lg text-muted-foreground">Four simple steps to your finished book</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                <div className="text-center space-y-4">
                  <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl gradient-accent text-white text-2xl font-bold material-shadow-lg">
                    {step.step}
                  </div>
                  <h3 className="text-xl font-semibold text-foreground">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-[calc(50%+2rem)] w-[calc(100%-4rem)] h-0.5 bg-gradient-to-r from-accent to-primary" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-primary to-accent text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center relative">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">Ready to Create Your Book?</h2>
          <p className="text-xl mb-8 text-white/90">
            Join thousands of authors using AI to bring their ideas to life faster than ever.
          </p>
          <Link to="/create">
            <MaterialButton variant="secondary" size="lg">
              <BookOpen className="h-5 w-5" />
              Get Started Now
            </MaterialButton>
          </Link>
        </div>
      </section>
    </div>
  );
}
