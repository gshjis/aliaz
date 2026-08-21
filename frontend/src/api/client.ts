// Обёртка над fetch: добавляет Authorization, обрабатывает 401 через refresh.

import { useAuthStore } from '../store/authStore';
import type { TokenResponse } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

// Флаг, чтобы не запускать refresh параллельно несколько раз.
let refreshPromise: Promise<string | null> | null = null;

/**
 * Попытаться обновить access_token через /auth/refresh.
 * Возвращает новый access_token или null при неудаче.
 */
async function tryRefresh(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as TokenResponse;
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}

/**
 * Выполнить запрос к API с авторизацией и автоматическим refresh при 401.
 * При неудачном refresh выполняет logout.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const accessToken = useAuthStore.getState().accessToken;

  const headers = new Headers(options.headers);
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  // Токен истёк — пробуем refresh и повторяем запрос один раз.
  if (res.status === 401 && accessToken) {
    refreshPromise = refreshPromise ?? tryRefresh();
    const newToken = await refreshPromise;
    refreshPromise = null;

    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    } else {
      useAuthStore.getState().logout();
      throw new ApiRequestError(401, 'Сессия истекла');
    }
  }

  if (!res.ok) {
    let detail = `Ошибка ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // тело не JSON — оставляем дефолтное сообщение
    }
    throw new ApiRequestError(res.status, detail);
  }

  // 204 No Content — возвращаем undefined.
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Ошибка запроса к API с HTTP-кодом и detail. */
export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
  }
}