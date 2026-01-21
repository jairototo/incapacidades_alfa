/**
 * Página principal del portal externo.
 * 
 * Permite al usuario elegir entre:
 * - Consultar estado de incapacidades existentes
 * - Radicar nuevas incapacidades
 * 
 * Características:
 * - Layout responsivo (grid 2 columnas → stack en mobile)
 * - Cards interactivas con hover effects
 * - Navegación con React Router
 */

import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Search, FileText, ArrowRight } from 'lucide-react';

export function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
              Sistema de Gestión de Incapacidades
            </h1>
            <p className="text-lg text-gray-600">
              Portal de autogestión para trabajadores y afiliados
            </p>
          </div>
        </div>
      </header>

      {/* Contenido principal */}
      <main className="container mx-auto px-4 py-12 md:py-20">
        <div className="max-w-5xl mx-auto">
          {/* Texto introductorio */}
          <div className="text-center mb-12">
            <h2 className="text-2xl font-semibold text-gray-900 mb-3">
              ¿Qué deseas hacer hoy?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Selecciona una opción para continuar. Puedes consultar el estado de tus 
              incapacidades o radicar una nueva.
            </p>
          </div>

          {/* Grid de opciones */}
          <div className="grid md:grid-cols-2 gap-6 md:gap-8">
            {/* Card: Consultar Incapacidad */}
            <Card 
              className="group hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-blue-500"
              onClick={() => navigate('/consultar')}
            >
              <CardHeader className="text-center pb-4">
                <div className="mx-auto mb-4 w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center group-hover:bg-blue-500 transition-colors">
                  <Search className="h-8 w-8 text-blue-600 group-hover:text-white transition-colors" />
                </div>
                <CardTitle className="text-2xl">Consultar Incapacidad</CardTitle>
                <CardDescription className="text-base mt-2">
                  Consulta el estado de tus incapacidades radicadas
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">✓</span>
                    <span>Busca por número de radicación</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">✓</span>
                    <span>Busca por documento de identidad</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">✓</span>
                    <span>Descarga documentos asociados</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">✓</span>
                    <span>Revisa historial de estados</span>
                  </li>
                </ul>
                <Button 
                  className="w-full mt-4 group-hover:bg-blue-600 transition-colors"
                  size="lg"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/consultar');
                  }}
                >
                  Consultar ahora
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            {/* Card: Radicar Incapacidad */}
            <Card 
              className="group hover:shadow-xl transition-all duration-300 cursor-pointer border-2 hover:border-green-500"
              onClick={() => navigate('/radicar')}
            >
              <CardHeader className="text-center pb-4">
                <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center group-hover:bg-green-500 transition-colors">
                  <FileText className="h-8 w-8 text-green-600 group-hover:text-white transition-colors" />
                </div>
                <CardTitle className="text-2xl">Radicar Incapacidad</CardTitle>
                <CardDescription className="text-base mt-2">
                  Inicia el proceso de radicación de una nueva incapacidad
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-0.5">✓</span>
                    <span>Wizard guiado paso a paso</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-0.5">✓</span>
                    <span>Carga de documentos soportes</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-0.5">✓</span>
                    <span>Validación en tiempo real</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-0.5">✓</span>
                    <span>Número de radicación inmediato</span>
                  </li>
                </ul>
                <Button 
                  className="w-full mt-4 bg-green-600 hover:bg-green-700 group-hover:bg-green-700 transition-colors"
                  size="lg"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/radicar');
                  }}
                >
                  Radicar ahora
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Información adicional */}
          <div className="mt-12 text-center">
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <p className="text-sm text-gray-700 mb-2">
                  <strong>¿Necesitas ayuda?</strong>
                </p>
                <p className="text-sm text-gray-600">
                  Si tienes dudas sobre el proceso, puedes comunicarte con nuestra línea de 
                  atención al usuario o consultar nuestras preguntas frecuentes.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center text-sm text-gray-600">
            Sistema de Gestión de Incapacidades © 2026 - Todos los derechos reservados
          </p>
        </div>
      </footer>
    </div>
  );
}
