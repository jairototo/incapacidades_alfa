import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { CorporateFooter } from '@/components/layout/CorporateFooter';
import { AppLayout } from '@/components/layout/AppLayout';

describe('CorporateFooter', () => {
  it('renders the corporate copyright and version', () => {
    render(<CorporateFooter />);
    expect(screen.getByText(/© 2026 Seguros Alfa/i)).toBeInTheDocument();
    expect(screen.getByText(/v\d/)).toBeInTheDocument();
  });
});

describe('AppLayout', () => {
  it('renders the routed content and the corporate footer', () => {
    render(
      <MemoryRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<div>CONTENIDO</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('CONTENIDO')).toBeInTheDocument();
    expect(screen.getByText(/© 2026 Seguros Alfa/i)).toBeInTheDocument();
  });
});
