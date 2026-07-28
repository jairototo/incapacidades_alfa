import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';

interface PasswordRevealDialogProps {
  open: boolean;
  username: string;
  password: string;
  onClose: () => void;
}

export function PasswordRevealDialog({ open, username, password, onClose }: PasswordRevealDialogProps) {
  const { toast } = useToast();
  const [confirmed, setConfirmed] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: 'Error al copiar', description: 'No se pudo copiar al portapapeles', variant: 'destructive' });
    }
  };

  const handleClose = () => {
    if (!confirmed) return;
    setConfirmed(false);
    onClose();
  };

  return (
    <Dialog open={open}>
      <DialogContent onInteractOutside={(e) => e.preventDefault()} onEscapeKeyDown={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>Credenciales generadas</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-3">
            Esta contraseña no se volverá a mostrar. Cópiala ahora y compártela de forma segura.
          </p>
          <div className="space-y-1">
            <span className="text-sm text-slate-500">Usuario</span>
            <p className="font-mono text-sm bg-slate-100 rounded px-2 py-1 select-all">{username}</p>
          </div>
          <div className="space-y-1">
            <span className="text-sm text-slate-500">Contraseña</span>
            <div className="flex items-center gap-2">
              <p className="font-mono text-sm bg-slate-100 rounded px-2 py-1 select-all flex-1">{password}</p>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? 'Copiado' : 'Copiar'}
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-2">
            <Checkbox id="confirm-copied" checked={confirmed} onCheckedChange={(v) => setConfirmed(v === true)} />
            <label htmlFor="confirm-copied" className="text-sm">Copié la contraseña</label>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleClose} disabled={!confirmed}>Cerrar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
