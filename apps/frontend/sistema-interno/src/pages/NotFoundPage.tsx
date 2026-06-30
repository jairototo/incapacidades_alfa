import { useNavigate } from 'react-router-dom';
import { FileQuestion } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * Página 404 - Ruta no encontrada
 */
export function NotFoundPage() {
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-slate-500 rounded-full flex items-center justify-center">
              <FileQuestion className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-lg font-bold">
            Página No Encontrada
          </CardTitle>
          <CardDescription>
            Error 404
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center text-sm text-slate-600">
            <p>
              La página que buscas no existe o ha sido movida.
            </p>
            <p className="mt-2">
              Verifica la URL o usa los botones de abajo para navegar.
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <Button onClick={handleGoHome} className="w-full">
              Ir al Dashboard
            </Button>
            <Button onClick={handleGoBack} variant="outline" className="w-full">
              Volver
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
