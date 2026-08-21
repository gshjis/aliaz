// Функции для работы с эндпоинтами аутентификации.

import { apiFetch } from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, UserResponse } from '../types';

/** Зарегистрировать нового пользователя и получить токены. */
export function register(payload: RegisterRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** Войти по email+password и получить токены. */
export function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** Обновить пару токенов по refresh_token. */
export function refresh(refreshToken: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

/** Получить данные текущего пользователя. */
export function me(): Promise<UserResponse> {
  return apiFetch<UserResponse>('/auth/me');
}