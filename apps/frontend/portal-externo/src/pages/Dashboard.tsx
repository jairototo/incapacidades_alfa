import { Link } from 'react-router-dom';
import { FileText, Files, Search } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { Card } from '@/components/ui/Card';

const actions = [
  {
    to: '/radicar/individual',
    title: 'Radicación Individual',
    desc: 'Radique una incapacidad para un empleado.',
    icon: FileText,
  },
  {
    to: '/radicar/masiva',
    title: 'Radicación Masiva',
    desc: 'Cargue múltiples incapacidades vía Excel.',
    icon: Files,
  },
  {
    to: '/consulta',
    title: 'Consulta de Incapacidades',
    desc: 'Revise el estado de sus radicaciones.',
    icon: Search,
  },
];

export function Dashboard() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">
          Hola, {user?.empresa?.razon_social ?? user?.nombre_completo}
        </h1>
        <p className="text-sm text-muted-foreground">¿Qué desea realizar hoy?</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-3">
        {actions.map(({ to, title, desc, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            aria-label={title}
            className="group transition-all duration-200 hover:-translate-y-0.5"
          >
            <Card className="h-full p-6 shadow-sm hover:shadow-md border-border">
              <Icon className="h-8 w-8 text-primary mb-3" />
              <h2 className="font-bold text-foreground">{title}</h2>
              <p className="text-sm text-muted-foreground mt-1">{desc}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
