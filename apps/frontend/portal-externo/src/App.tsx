import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { Dashboard } from '@/pages/Dashboard';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { RadicacionIndividualPage } from '@/components/radicacion/RadicacionIndividualPage';
import { RadicacionMasivaPage } from '@/components/radicacion/masiva/RadicacionMasivaPage';
import { ConsultaEmpresa } from '@/pages/ConsultaEmpresa';
import { AppLayout } from '@/components/layout/AppLayout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
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
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/radicar/individual" element={<RadicacionIndividualPage />} />
              <Route path="/radicar/masiva" element={<RadicacionMasivaPage />} />
              <Route path="/consulta" element={<ConsultaEmpresa />} />
            </Route>
          </Route>
          {/* Retire old public routes */}
          <Route path="/radicar" element={<Navigate to="/login" replace />} />
          <Route path="/consultar" element={<Navigate to="/consulta" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
