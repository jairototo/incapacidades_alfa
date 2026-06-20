import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProrrogaSwitch } from '@/components/radicacion/ProrrogaSwitch';

describe('ProrrogaSwitch', () => {
  it('toggles on click and reflects checked state', () => {
    const onChange = vi.fn();
    const { rerender } = render(<ProrrogaSwitch checked={false} onChange={onChange} />);
    const sw = screen.getByRole('switch');
    expect(sw).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(sw);
    expect(onChange).toHaveBeenCalledWith(true);
    rerender(<ProrrogaSwitch checked={true} onChange={onChange} />);
    expect(screen.getByRole('switch')).toHaveAttribute('aria-checked', 'true');
  });
});
