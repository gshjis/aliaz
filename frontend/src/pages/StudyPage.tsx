// Страница «Изучение по карточкам»: настройка → карточки → тест.

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import StudyCard from '../components/StudyCard';
import MatchingTest from '../components/MatchingTest';
import { listWords } from '../api/words';
import { ApiRequestError } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { pickWords } from '../study/study';
import type { WordResponse } from '../types';

const DEFAULT_COUNT = 10;

export default function StudyPage() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  const [words, setWords] = useState<WordResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [count, setCount] = useState(DEFAULT_COUNT);
  const [session, setSession] = useState<WordResponse[] | null>(null);
  const [cardIndex, setCardIndex] = useState(0);
  const [phase, setPhase] = useState<'setup' | 'cards' | 'test'>('setup');

  const loadWords = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listWords();
      setWords(data);
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        logout();
        navigate('/login');
      } else if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadWords();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startSession = () => {
    const picked = pickWords(words, Math.min(count, words.length));
    setSession(picked);
    setCardIndex(0);
    setPhase('cards');
  };

  const restartSession = () => {
    startSession();
  };

  const goHome = () => {
    navigate('/');
  };

  const maxCount = Math.min(DEFAULT_COUNT, words.length);

  if (loading) {
    return (
      <Layout>
        <p>Загрузка…</p>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <p className="error">{error}</p>
      </Layout>
    );
  }

  if (words.length === 0) {
    return (
      <Layout>
        <h2>Изучение по карточкам</h2>
        <p className="empty">Слов пока нет. Добавьте слова на главной странице!</p>
        <button type="button" className="btn btn-outline" onClick={goHome}>
          На главную
        </button>
      </Layout>
    );
  }

  if (phase === 'cards' && session) {
    const word = session[cardIndex];
    return (
      <Layout>
        <p className="study-progress">
          Карточка {cardIndex + 1} из {session.length}
        </p>
        <StudyCard word={word} />
        <div className="study-actions">
          {cardIndex > 0 && (
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => setCardIndex((i) => i - 1)}
            >
              Назад
            </button>
          )}
          {cardIndex + 1 < session.length ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setCardIndex((i) => i + 1)}
            >
              Далее
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setPhase('test')}
            >
              К тесту
            </button>
          )}
        </div>
      </Layout>
    );
  }

  if (phase === 'test' && session) {
    return (
      <Layout>
        <MatchingTest
          words={session}
          onRestart={restartSession}
          onHome={goHome}
        />
      </Layout>
    );
  }

  return (
    <Layout>
      <h2>Изучение по карточкам</h2>
      <p className="empty">Сколько слов хотите изучить?</p>
      <div className="study-setup">
        <label htmlFor="study-count" className="study-label">
          Количество слов
        </label>
        <select
          id="study-count"
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
        >
          {Array.from({ length: maxCount }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
        <button type="button" className="btn btn-primary" onClick={startSession}>
          Начать
        </button>
      </div>
    </Layout>
  );
}