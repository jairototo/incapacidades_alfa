import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { Upload, FileIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { validateFile, formatFileSize } from '@/lib/fileHelpers';

export interface FileUploadProps {
  onFileSelect: (files: File[]) => void;
  accept?: string;
  maxSize?: number; // en bytes
  maxFiles?: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  error?: string;
}

export function FileUpload({
  onFileSelect,
  accept = '.pdf,.jpg,.jpeg,.png',
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 10,
  multiple = true,
  disabled = false,
  className,
  error,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | undefined>(error);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      handleFiles(selectedFiles);
    }
  };

  const handleFiles = (files: File[]) => {
    setValidationError(undefined);

    // Validar cantidad de archivos
    if (files.length > maxFiles) {
      setValidationError(`Solo se permiten hasta ${maxFiles} archivos`);
      return;
    }

    // Validar cada archivo
    const validFiles: File[] = [];
    for (const file of files) {
      const validation = validateFile(file, maxSize);
      if (!validation.valid) {
        setValidationError(validation.error);
        return;
      }
      validFiles.push(file);
    }

    // Si todos los archivos son válidos, notificar al padre
    if (validFiles.length > 0) {
      onFileSelect(validFiles);
      // Limpiar el input para permitir seleccionar el mismo archivo nuevamente
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    }
  };

  const handleClick = () => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  };

  return (
    <div className={cn('w-full', className)}>
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-8 transition-colors cursor-pointer',
          'hover:border-blue-400 hover:bg-blue-50',
          isDragging && 'border-blue-500 bg-blue-50',
          disabled && 'opacity-50 cursor-not-allowed hover:border-gray-300 hover:bg-transparent',
          (validationError || error) && 'border-red-300 bg-red-50',
          !isDragging && !disabled && !validationError && !error && 'border-gray-300 bg-gray-50'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
          aria-label="Seleccionar archivos"
        />

        <div className="flex flex-col items-center justify-center text-center space-y-3">
          <div className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center',
            isDragging ? 'bg-blue-100' : 'bg-gray-100'
          )}>
            {isDragging ? (
              <FileIcon className="w-6 h-6 text-blue-600" />
            ) : (
              <Upload className="w-6 h-6 text-gray-600" />
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-gray-700">
              {isDragging ? (
                'Suelta los archivos aquí'
              ) : (
                <>
                  <span className="text-blue-600 hover:text-blue-700">Selecciona archivos</span>
                  {' o arrástralos aquí'}
                </>
              )}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              PDF, JPG, PNG (máx. {formatFileSize(maxSize)})
            </p>
          </div>
        </div>
      </div>

      {(validationError || error) && (
        <p className="mt-2 text-sm text-red-600">
          {validationError || error}
        </p>
      )}
    </div>
  );
}
