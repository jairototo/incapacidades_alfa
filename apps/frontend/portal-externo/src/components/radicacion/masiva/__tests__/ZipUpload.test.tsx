import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ZipUpload } from '@/components/radicacion/masiva/ZipUpload';

describe('ZipUpload', () => {
  it('rejects a ZIP over 20MB', () => {
    const onZip = vi.fn();
    render(<ZipUpload onZipSelected={onZip} />);
    const big = new File([new Uint8Array(21 * 1024 * 1024)], 'big.zip', { type: 'application/zip' });
    fireEvent.change(screen.getByLabelText(/zip/i), { target: { files: [big] } });
    expect(screen.getByText(/20 MB/)).toBeInTheDocument();
    expect(onZip).not.toHaveBeenCalled();
  });

  it('accepts a ZIP under 20MB and calls back', () => {
    const onZip = vi.fn();
    render(<ZipUpload onZipSelected={onZip} />);
    const small = new File([new Uint8Array(1024)], 'docs.zip', { type: 'application/zip' });
    fireEvent.change(screen.getByLabelText(/zip/i), { target: { files: [small] } });
    expect(onZip).toHaveBeenCalledWith(small);
  });
});
