import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { empleadoService } from '@/services/empleadoService';
import type { ValidacionMasivaResponse, ConfirmacionMasivaResponse } from '@/types/empleado';

interface CargaMasivaWizardProps {
  open: boolean;
  onClose: () => void;
}

type Step = 1 | 2 | 3;

export function CargaMasivaWizard({ open, onClose }: CargaMasivaWizardProps) {
  const [step, setStep] = useState<Step>(1);
  const [file, setFile] = useState<File | null>(null);
  const [validando, setValidando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [validacion, setValidacion] = useState<ValidacionMasivaResponse | null>(null);
  const [confirmacion, setConfirmacion] = useState<ConfirmacionMasivaResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDescargarPlantilla = async () => {
    const blob = await empleadoService.getPlantilla();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'plantilla_empleados.xlsx';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleValidar = async () => {
    if (!file) return;
    setValidando(true);
    setErrorMessage(null);
    try {
      const result = await empleadoService.validarCargaMasiva(file);
      setValidacion(result);
      setStep(2);
    } catch {
      setErrorMessage('No se pudo validar el archivo. Verifica el formato e inténtalo de nuevo.');
    } finally {
      setValidando(false);
    }
  };

  const handleConfirmar = async () => {
    if (!file) return;
    setConfirmando(true);
    setErrorMessage(null);
    try {
      const result = await empleadoService.confirmarCargaMasiva(file);
      setConfirmacion(result);
      setStep(3);
    } catch {
      setErrorMessage('No se pudo confirmar la carga. Inténtalo de nuevo.');
    } finally {
      setConfirmando(false);
    }
  };

  const handleClose = () => {
    setStep(1);
    setFile(null);
    setValidacion(null);
    setConfirmacion(null);
    setErrorMessage(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Carga masiva de empleados — Paso {step} de 3</DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-4">
            <Button variant="outline" onClick={handleDescargarPlantilla}>Descargar plantilla</Button>
            <div className="space-y-2">
              <Label htmlFor="carga-masiva-archivo">Archivo (.xlsx)</Label>
              <input
                id="carga-masiva-archivo"
                type="file"
                accept=".xlsx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm"
              />
            </div>
            {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
            <DialogFooter>
              <Button onClick={handleValidar} disabled={!file || validando}>Validar</Button>
            </DialogFooter>
          </div>
        )}

        {step === 2 && validacion && (
          <div className="space-y-4">
            <p className="text-sm">
              {validacion.total_filas} filas totales · {validacion.validas} válidas · {validacion.con_error} con error
            </p>
            {validacion.errores.length > 0 && (
              <div className="max-h-64 overflow-auto border rounded">
                <Table>
                  <TableHeader>
                    <TableRow><TableHead>Fila</TableHead><TableHead>Columna</TableHead><TableHead>Mensaje</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>
                    {validacion.errores.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell>{e.fila}</TableCell>
                        <TableCell>{e.columna ?? '—'}</TableCell>
                        <TableCell>{e.mensaje}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
            <DialogFooter className="justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>Volver</Button>
              <Button onClick={handleConfirmar} disabled={validacion.validas === 0 || confirmando}>
                Confirmar carga
              </Button>
            </DialogFooter>
          </div>
        )}

        {step === 3 && confirmacion && (
          <div className="space-y-4">
            <p className="text-sm">
              {confirmacion.insertadas} insertadas · {confirmacion.con_error} con error
            </p>
            {confirmacion.errores.length > 0 && (
              <div className="max-h-64 overflow-auto border rounded">
                <Table>
                  <TableHeader>
                    <TableRow><TableHead>Fila</TableHead><TableHead>Columna</TableHead><TableHead>Mensaje</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>
                    {confirmacion.errores.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell>{e.fila}</TableCell>
                        <TableCell>{e.columna ?? '—'}</TableCell>
                        <TableCell>{e.mensaje}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            <DialogFooter>
              <Button onClick={handleClose}>Cerrar</Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
