// Вспомогательная логика для режима «Изучение по карточкам».

import type { WordResponse } from '../types';

/** Перемешать массив (Fisher–Yates). Возвращает новый массив. */
export function shuffle<T>(arr: T[]): T[] {
  const result = [...arr];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

/** Выбрать до count случайных слов из списка. */
export function pickWords(words: WordResponse[], count: number): WordResponse[] {
  return shuffle(words).slice(0, count);
}

/** Сделать первую букву заглавной. */
export function capitalize(word: string): string {
  if (word.length === 0) return word;
  return word[0].toUpperCase() + word.slice(1);
}

/** Собрать 4 варианта перевода: правильный + 3 случайных из пула. */
export function buildOptions(word: WordResponse, pool: WordResponse[]): string[] {
  const correct = word.translation;
  const others = shuffle(pool)
    .filter((w) => w.id !== word.id && w.translation !== correct)
    .map((w) => w.translation)
    .slice(0, 3);
  return shuffle([correct, ...others]);
}