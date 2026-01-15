import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RadicarIncapacidadWizard } from '@/components/wizard/RadicarIncapacidadWizard';

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
      <RadicarIncapacidadWizard />
    </QueryClientProvider>
  );
}

export default App;


