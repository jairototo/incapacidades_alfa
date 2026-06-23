import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PendienteAlertBadge } from '../PendienteAlertBadge';

describe('PendienteAlertBadge', () => {
  it('renders nothing when diasEnPendiente is below threshold (< 8)', () => {
    const { container } = render(<PendienteAlertBadge diasEnPendiente={3} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when diasEnPendiente is 7 (one below threshold)', () => {
    const { container } = render(<PendienteAlertBadge diasEnPendiente={7} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the badge at exactly 8 days (threshold boundary)', () => {
    render(<PendienteAlertBadge diasEnPendiente={8} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/8 días sin respuesta/i)).toBeInTheDocument();
  });

  it('renders the badge when diasEnPendiente exceeds 8', () => {
    render(<PendienteAlertBadge diasEnPendiente={15} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/15 días sin respuesta/i)).toBeInTheDocument();
  });

  it('shows the correct number of days in the badge text', () => {
    render(<PendienteAlertBadge diasEnPendiente={12} />);
    expect(screen.getByText(/12 días sin respuesta/i)).toBeInTheDocument();
  });

  it('applies the correct red styling classes', () => {
    render(<PendienteAlertBadge diasEnPendiente={10} />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-red-100');
    expect(badge).toHaveClass('text-red-800');
    expect(badge).toHaveClass('rounded-full');
  });

  it('has accessible aria-label containing the day count', () => {
    render(<PendienteAlertBadge diasEnPendiente={9} />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', expect.stringContaining('9'));
  });
});
