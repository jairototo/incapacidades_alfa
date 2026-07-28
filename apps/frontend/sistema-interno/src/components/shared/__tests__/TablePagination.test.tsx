import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablePagination } from '../TablePagination';

describe('TablePagination', () => {
  it('disables "Anterior" on the first page (skip=0)', () => {
    render(<TablePagination skip={0} limit={100} resultCount={100} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /anterior/i })).toBeDisabled();
  });

  it('enables "Anterior" when skip > 0', () => {
    render(<TablePagination skip={100} limit={100} resultCount={50} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /anterior/i })).not.toBeDisabled();
  });

  it('disables "Siguiente" when the page came back incomplete', () => {
    render(<TablePagination skip={0} limit={100} resultCount={42} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /siguiente/i })).toBeDisabled();
  });

  it('enables "Siguiente" when the page came back full', () => {
    render(<TablePagination skip={0} limit={100} resultCount={100} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /siguiente/i })).not.toBeDisabled();
  });

  it('calls onNext/onPrev when clicked', () => {
    const onNext = vi.fn();
    const onPrev = vi.fn();
    render(<TablePagination skip={100} limit={100} resultCount={100} onPrev={onPrev} onNext={onNext} />);
    fireEvent.click(screen.getByRole('button', { name: /siguiente/i }));
    fireEvent.click(screen.getByRole('button', { name: /anterior/i }));
    expect(onNext).toHaveBeenCalledTimes(1);
    expect(onPrev).toHaveBeenCalledTimes(1);
  });
});
