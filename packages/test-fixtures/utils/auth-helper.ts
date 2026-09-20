import { type APIRequestContext, expect } from '@playwright/test';

export interface AuthSession {
  token: string;
  userId: string;
}

export async function authenticateViaApi(
  request: APIRequestContext,
  username: string = 'qa-engineer@antigravity.internal',
  password: string = 'SuperSecret123!'
): Promise<AuthSession> {
  const response = await request.post('/api/auth/token', {
    data: { username, password },
  });

  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  return {
    token: data.token,
    userId: data.user.id,
  };
}

