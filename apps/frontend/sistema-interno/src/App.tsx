import { Toaster } from '@/components/ui/toaster';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        <h1 className="text-4xl font-bold text-center mb-8">
          Sistema Interno - Incapacidades
        </h1>
        <div className="text-center text-muted-foreground">
          <p>Proyecto configurado correctamente ✓</p>
          <p className="mt-2">
            React 19 + TypeScript + Vite + TailwindCSS + Shadcn/ui
          </p>
        </div>
      </div>
      <Toaster />
    </div>
  );
}

export default App;
