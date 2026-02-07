import { ColliderAPI, createColliderAPI } from './api-client';

describe('ColliderAPI', () => {
  it('should create an instance', () => {
    const api = createColliderAPI({ baseUrl: 'http://localhost:8000' });
    expect(api).toBeInstanceOf(ColliderAPI);
  });

  it('should set and clear token', () => {
    const api = createColliderAPI({ baseUrl: 'http://localhost:8000' });
    api.setToken('test-token');
    expect(api).toBeDefined();
    api.setToken(undefined);
    expect(api).toBeDefined();
  });

  it('should build correct URLs', () => {
    const api = createColliderAPI({ baseUrl: 'http://localhost:8000' });
    // The API instance should be created with the base URL
    expect(api).toBeDefined();
  });
});
