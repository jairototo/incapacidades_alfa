import { useState } from 'react';

const MAX = 20 * 1024 * 1024;

export function ZipUpload({ onZipSelected }: { onZipSelected: (file: File) => void }) {
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="rounded-lg border border-dashed border-input p-4">
      <label htmlFor="zip-input" className="block text-sm font-medium text-foreground mb-2">
        Cargar ZIP de documentos (máx 20MB) — nombres: {'{documento}_{TIPO}.ext'}
      </label>
      <input id="zip-input" type="file" accept=".zip" aria-label="zip"
        onChange={(e) => {
          const f = e.target.files?.[0]; if (!f) return;
          if (f.size > MAX) { setError('El ZIP excede el máximo de 20 MB'); return; }
          setError(null); onZipSelected(f);
        }} />
      {error && <p className="text-sm text-[#D92D20] mt-2">{error}</p>}
    </div>
  );
}
