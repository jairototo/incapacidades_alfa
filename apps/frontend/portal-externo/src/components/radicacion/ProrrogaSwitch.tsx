import { Label } from '@/components/ui/Label';

interface Props {
  checked: boolean;
  onChange: (v: boolean) => void;
}

export function ProrrogaSwitch({ checked, onChange }: Props) {
  return (
    <div className="flex items-center justify-between rounded-md border border-input p-3">
      <div>
        <Label htmlFor="prorroga">¿Es una prórroga?</Label>
        <p className="text-xs text-muted-foreground">
          Active si esta incapacidad es continuación de una anterior.
        </p>
      </div>
      <button
        id="prorroga"
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${checked ? 'bg-primary' : 'bg-gray-300'}`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`}
        />
      </button>
    </div>
  );
}
