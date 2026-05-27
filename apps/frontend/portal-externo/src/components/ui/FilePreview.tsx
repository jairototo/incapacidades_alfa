import { FileText, Image as ImageIcon, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatFileSize, isImageFile, isPdfFile } from '@/lib/fileHelpers';

export interface FilePreviewProps {
  file: File;
  onRemove?: () => void;
  showRemove?: boolean;
  className?: string;
}

export function FilePreview({
  file,
  onRemove,
  showRemove = true,
  className,
}: FilePreviewProps) {
  const isImage = isImageFile(file);
  const isPdf = isPdfFile(file);

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-3 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors',
        className
      )}
    >
      {/* Icono según tipo de archivo */}
      <div className={cn(
        'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center',
        isImage && 'bg-blue-100',
        isPdf && 'bg-red-100'
      )}>
        {isImage && <ImageIcon className="w-5 h-5 text-blue-600" />}
        {isPdf && <FileText className="w-5 h-5 text-red-600" />}
        {!isImage && !isPdf && <FileText className="w-5 h-5 text-gray-600" />}
      </div>

      {/* Información del archivo */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {file.name}
        </p>
        <p className="text-xs text-gray-500">
          {formatFileSize(file.size)}
        </p>
      </div>

      {/* Botón eliminar */}
      {showRemove && onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="flex-shrink-0 w-8 h-8 rounded-full hover:bg-gray-200 flex items-center justify-center transition-colors group"
          aria-label="Eliminar archivo"
        >
          <X className="w-4 h-4 text-gray-500 group-hover:text-gray-700" />
        </button>
      )}
    </div>
  );
}

export interface FileListProps {
  files: File[];
  onRemove?: (index: number) => void;
  showRemove?: boolean;
  emptyMessage?: string;
  className?: string;
}

export function FileList({
  files,
  onRemove,
  showRemove = true,
  emptyMessage = 'No hay archivos cargados',
  className,
}: FileListProps) {
  if (files.length === 0) {
    return (
      <div className={cn('text-center py-6 text-sm text-gray-500', className)}>
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      {files.map((file, index) => (
        <FilePreview
          key={`${file.name}-${index}`}
          file={file}
          onRemove={onRemove ? () => onRemove(index) : undefined}
          showRemove={showRemove}
        />
      ))}
    </div>
  );
}
