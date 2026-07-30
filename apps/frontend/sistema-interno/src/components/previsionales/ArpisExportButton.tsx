/**
 * ArpisExportButton — descarga el libro de cargue ARPIS de un lote
 * (`GET /previsionales/lotes/{id}/arpis.xlsx`, `previsionalesService.exportarArpis`).
 *
 * El backend arma el workbook completo de forma síncrona en la misma
 * petición (no hay job en background), así que el botón necesita un estado
 * de carga explícito mientras la respuesta llega.
 *
 * Descarga: sigue el mismo patrón de blob autenticado que
 * `DetalleModal.tsx` (`handleDownloadDocument`, líneas ~63-80) --
 * `URL.createObjectURL` + `<a>` sintético + `URL.revokeObjectURL` -- en vez
 * de reinventar la descarga.
 */
import { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { previsionalesService } from '@/services/previsionales';

interface ArpisExportButtonProps {
  loteId: string;
  /** `nombre_archivo` del lote, usado para nombrar el archivo descargado. */
  nombreArchivo?: string;
}

export function ArpisExportButton({ loteId, nombreArchivo }: ArpisExportButtonProps) {
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExportar = async () => {
    setError(null);
    setDescargando(true);
    try {
      const blob = await previsionalesService.exportarArpis(loteId);
      const base = (nombreArchivo ?? loteId).replace(/\.xlsx$/i, '');

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `arpis_${base}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      setError('No se pudo generar el archivo ARPIS. Intenta nuevamente.');
    } finally {
      setDescargando(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <Button variant="outline" onClick={handleExportar} disabled={descargando}>
        {descargando ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Generando ARPIS...
          </>
        ) : (
          <>
            <Download className="mr-2 h-4 w-4" />
            Exportar ARPIS
          </>
        )}
      </Button>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
