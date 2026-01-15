import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

// Configuración de React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold text-primary">
              Sistema de Gestión de Incapacidades
            </h1>
            <p className="text-lg text-muted-foreground">
              Portal de radicación y consulta de incapacidades médicas
            </p>
          </div>

          {/* Cards de Opciones */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Radicar Incapacidad</CardTitle>
                <CardDescription>
                  Registre una nueva incapacidad médica en el sistema
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="primary" className="w-full">
                  Iniciar Radicación
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Consultar Incapacidad</CardTitle>
                <CardDescription>
                  Consulte el estado de una incapacidad radicada
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  Consultar Estado
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Información Adicional */}
          <Card>
            <CardHeader>
              <CardTitle>Información del Proceso</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="font-semibold">Tipos de Incapacidad:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                  <li>
                    <strong>ARL:</strong> Accidentes de trabajo y enfermedades laborales
                  </li>
                  <li>
                    <strong>SALUD:</strong> Enfermedades generales y maternidad
                  </li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold">Documentos Requeridos:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                  <li>Certificado de incapacidad médica</li>
                  <li>Historia clínica (si aplica)</li>
                  <li>Documento de identidad</li>
                  <li>Soportes adicionales según el caso</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    </QueryClientProvider>
  );
}

export default App;

