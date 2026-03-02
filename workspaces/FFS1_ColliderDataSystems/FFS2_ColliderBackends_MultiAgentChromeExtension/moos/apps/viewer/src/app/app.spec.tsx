import { render } from '@testing-library/react';

import App from './app';

describe('App', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<App />);
    expect(baseElement).toBeTruthy();
  });

  it('should render scaffold title and contract rows', () => {
    const { getByText } = render(<App />);
    expect(getByText('MOOS Viewer')).toBeTruthy();
    expect(getByText('sidepanel-link')).toBeTruthy();
    expect(getByText('sidepanel-link-age')).toBeTruthy();
    expect(getByText('sidepanel-link-health')).toBeTruthy();
    expect(getByText('bootstrap-preview')).toBeTruthy();
    expect(getByText('journey-probe')).toBeTruthy();
    expect(getByText('contract')).toBeTruthy();
  });
});
