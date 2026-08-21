// Функции для работы с эндпоинтами слов.

import { apiFetch } from './client';
import type { WordCreateRequest, WordResponse } from '../types';

/** Создать слово (перевод/транскрипция вычисляются на бэкенде). */
export function createWord(payload: WordCreateRequest): Promise<WordResponse> {
  return apiFetch<WordResponse>('/words', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** Получить список слов текущего пользователя. */
export function listWords(): Promise<WordResponse[]> {
  return apiFetch<WordResponse[]>('/words');
}

/** Получить одно слово по id. */
export function getWord(wordId: number): Promise<WordResponse> {
  return apiFetch<WordResponse>(`/words/${wordId}`);
}

/** Удалить слово по id. */
export function deleteWord(wordId: number): Promise<void> {
  return apiFetch<void>(`/words/${wordId}`, { method: 'DELETE' });
}