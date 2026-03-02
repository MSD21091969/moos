import { render } from '@testing-library/react';

import App from './app';

describe('App', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<App />);
    expect(baseElement).toBeTruthy();
  });

  it('should render scaffold title and contract rows', () => {
    const { getByText } = render(<App />);
    expect(getByText('MOOS Sidepanel')).toBeTruthy();
    expect(getByText('viewer-link')).toBeTruthy();
    expect(getByText('viewer-link-age')).toBeTruthy();
    expect(getByText('viewer-link-health')).toBeTruthy();
    expect(getByText('data-server')).toBeTruthy();
    expect(getByText('journey-probe')).toBeTruthy();
    expect(getByText('contract')).toBeTruthy();
  });
});
