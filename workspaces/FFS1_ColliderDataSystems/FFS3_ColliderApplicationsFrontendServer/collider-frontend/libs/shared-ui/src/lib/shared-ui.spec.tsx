import { render } from '@testing-library/react';

import ColliderFrontendSharedUi from './shared-ui';

describe('ColliderFrontendSharedUi', () => {
  it('should render successfully', () => {
    const { baseElement } = render(<ColliderFrontendSharedUi />);
    expect(baseElement).toBeTruthy();
  });
});
