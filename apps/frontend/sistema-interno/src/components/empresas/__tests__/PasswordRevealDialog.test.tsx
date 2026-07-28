import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PasswordRevealDialog } from '../PasswordRevealDialog';

describe('PasswordRevealDialog', () => {
  it('shows username and password', () => {
    render(<PasswordRevealDialog open username="900123456" password="Abc12345xyz" onClose={vi.fn()} />);
    expect(screen.getByText('900123456')).toBeInTheDocument();
    expect(screen.getByText('Abc12345xyz')).toBeInTheDocument();
  });

  it('keeps "Cerrar" disabled until the confirmation checkbox is checked', () => {
    render(<PasswordRevealDialog open username="u" password="p" onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: /cerrar/i })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(screen.getByRole('button', { name: /cerrar/i })).not.toBeDisabled();
  });

  it('calls onClose only after the checkbox is checked and Cerrar is clicked', () => {
    const onClose = vi.fn();
    render(<PasswordRevealDialog open username="u" password="p" onClose={onClose} />);
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: /cerrar/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
