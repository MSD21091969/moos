import { render } from '@testing-library/react';

import ColliderFrontendNodeContainer from './node-container';

describe('ColliderFrontendNodeContainer', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<ColliderFrontendNodeContainer />);
    expect(baseElement).toBeTruthy();
  });
});
