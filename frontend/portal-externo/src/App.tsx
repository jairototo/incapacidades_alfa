import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Home } from '@/pages/Home';
import { ConsultarIncapacidad } from '@/pages/ConsultarIncapacidad';
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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/consultar" element={<ConsultarIncapacidad />} />
          <Route path="/radicar" element={<RadicarIncapacidadWizard />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;


