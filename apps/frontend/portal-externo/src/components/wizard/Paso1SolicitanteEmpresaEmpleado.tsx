import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Building2, User, UserCircle } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { paso1Schema, type Paso1FormData } from '@/schemas/radicacionSchema';

interface Paso1Props {
  initialData?: Partial<Paso1FormData>;
  onContinue: (data: Paso1FormData) => void;
  onCancel?: () => void;
}

/**
 * Paso 1 del wizard de radicación.
 * Captura datos del Solicitante, Empresa y Empleado sin búsqueda en BD.
 * Solo validaciones de formato. Empresa es opcional (independiente si se omite).
 */
export function Paso1SolicitanteEmpresaEmpleado({
  initialData,
  onContinue,
  onCancel,
}: Paso1Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Paso1FormData>({
    resolver: zodResolver(paso1Schema),
    defaultValues: initialData,
  });

  const onSubmit = (data: Paso1FormData) => {
    // Limpiar strings vacíos opcionales
    if (data.empresa && !data.empresa.nit && !data.empresa.nombre) {
      data.empresa = undefined;
    }
    onContinue(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* Título */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-foreground">Información del Solicitante</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Complete los datos de quien radica la incapacidad, la empresa y el empleado.
        </p>
      </div>

      {/* ── Sección Solicitante ─────────────────────────────────────────────── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <UserCircle className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">Solicitante</h3>
          <span className="text-xs text-muted-foreground font-normal ml-1">
            (quien diligencia el formulario)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Correo electrónico"
            type="email"
            {...register('solicitante.correo')}
            error={errors.solicitante?.correo?.message}
            placeholder="ejemplo@correo.com"
            required
          />
          <Input
            label="Nombres"
            {...register('solicitante.nombres')}
            error={errors.solicitante?.nombres?.message}
            placeholder="Nombres completos"
            required
          />
          <Input
            label="Apellidos"
            {...register('solicitante.apellidos')}
            error={errors.solicitante?.apellidos?.message}
            placeholder="Apellidos completos"
          />
          <Input
            label="Teléfono"
            {...register('solicitante.telefono')}
            error={errors.solicitante?.telefono?.message}
            placeholder="Ej: 3001234567"
          />
        </div>
      </section>

      {/* ── Sección Empresa ─────────────────────────────────────────────────── */}
      <section className="space-y-4 border-t pt-6">
        <div className="flex items-center gap-2">
          <Building2 className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">Empresa</h3>
          <span className="text-xs text-muted-foreground font-normal ml-1">
            (opcional — si no aplica, se asume trabajador independiente)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="NIT de la empresa"
            {...register('empresa.nit')}
            error={(errors.empresa as any)?.nit?.message}
            placeholder="Ej: 900123456-1"
          />
          <Input
            label="Nombre de la empresa"
            {...register('empresa.nombre')}
            error={(errors.empresa as any)?.nombre?.message}
            placeholder="Razón social"
          />
        </div>

        <p className="text-xs text-muted-foreground bg-muted rounded-md p-3">
          Si no pertenece a una empresa (trabajador independiente), puede dejar estos campos vacíos.
        </p>
      </section>

      {/* ── Sección Empleado ────────────────────────────────────────────────── */}
      <section className="space-y-4 border-t pt-6">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">Empleado / Afectado</h3>
          <span className="text-xs text-muted-foreground font-normal ml-1">
            (persona a quien se le radica la incapacidad)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Tipo de documento"
            {...register('empleado.tipo_documento')}
            error={errors.empleado?.tipo_documento?.message}
            required
          >
            <option value="">Seleccione</option>
            <option value="CC">Cédula de Ciudadanía (CC)</option>
            <option value="CE">Cédula de Extranjería (CE)</option>
            <option value="PA">Pasaporte (PA)</option>
            <option value="TI">Tarjeta de Identidad (TI)</option>
          </Select>

          <Input
            label="Número de documento"
            {...register('empleado.numero_documento')}
            error={errors.empleado?.numero_documento?.message}
            placeholder="Solo números"
            required
          />

          <Input
            label="Nombres"
            {...register('empleado.nombres')}
            error={errors.empleado?.nombres?.message}
            placeholder="Nombres completos"
            required
          />

          <Input
            label="Apellidos"
            {...register('empleado.apellidos')}
            error={errors.empleado?.apellidos?.message}
            placeholder="Apellidos completos"
          />

          <Input
            label="Correo electrónico"
            type="email"
            {...register('empleado.email')}
            error={errors.empleado?.email?.message}
            placeholder="empleado@correo.com"
          />

          <Input
            label="Teléfono"
            {...register('empleado.telefono')}
            error={errors.empleado?.telefono?.message}
            placeholder="Ej: 3001234567 (10 dígitos)"
          />
        </div>
      </section>

      {/* ── Navegación ──────────────────────────────────────────────────────── */}
      <div className="flex justify-between pt-6 border-t">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
        )}
        <Button type="submit" className="ml-auto" variant="primary">
          Continuar
        </Button>
      </div>
    </form>
  );
}
