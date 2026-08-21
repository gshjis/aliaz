// Типы ответов и запросов API (соответствуют схемам бэкенда).

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  nickname: string;
  email: string;
  telegram_nickname?: string | null;
}

export interface WordResponse {
  id: number;
  word_en: string;
  translation: string;
  transcription: string;
  corrected_word: string;
  language_swapped: boolean;
  created_at: string;
}

export interface WordCreateRequest {
  word_en: string;
  source_lang?: string;
  target_lang?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  nickname: string;
  email: string;
  password: string;
  telegram_nickname?: string;
}

export interface ApiError {
  detail: string;
}