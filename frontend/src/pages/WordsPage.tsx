// Страница слов: список, форма добавления, удаление.

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import WordCard from '../components/WordCard';
import { createWord, deleteWord, listWords } from '../api/words';
import { ApiRequestError } from '../api/client';
import { useAuthStore } from '../store/authStore';
import type { WordResponse } from '../types';

export default function WordsPage() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  const [words, setWords] = useState<WordResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [wordEn, setWordEn] = useState('');
  const [sourceLang, setSourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('ru');
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [swapNotice, setSwapNotice] = useState<string | null>(null);

  const swapLanguages = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
  };

  const loadWords = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listWords();
      setWords(data);
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        // refresh не удался — logout уже выполнен в client.ts
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

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError(null);
    setSwapNotice(null);
    setAdding(true);
    try {
      const created = await createWord({
        word_en: wordEn,
        source_lang: sourceLang,
        target_lang: targetLang,
      });
      if (created.language_swapped) {
        // Бэкенд уже перевёл в правильном направлении и исправил языки.
        setSwapNotice('Языки были перепутаны и автоматически исправлены.');
      }
      setWords((prev) => [created, ...prev]);
      setWordEn('');
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        logout();
        navigate('/login');
      } else if (err instanceof Error) {
        setAddError(err.message);
      }
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteWord(id);
      setWords((prev) => prev.filter((w) => w.id !== id));
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 401) {
        logout();
        navigate('/login');
      } else if (err instanceof Error) {
        setError(err.message);
      }
    }
  };

  return (
    <Layout>
      <h2>Мои слова</h2>

      <div className="study-entry">
        <Link to="/" className="btn btn-outline">
          Главная
        </Link>
        <Link to="/study" className="btn btn-primary">
          Изучение по карточкам
        </Link>
      </div>

      <form className="add-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Слово на английском"
          value={wordEn}
          onChange={(e) => setWordEn(e.target.value)}
          required
        />
        <select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}>
          <option value="en">en</option>
          <option value="ru">ru</option>
        </select>
        <button
          type="button"
          className="btn"
          onClick={swapLanguages}
          title="Поменять языки местами"
        >
          ⇄
        </button>
        <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
          <option value="ru">ru</option>
          <option value="en">en</option>
        </select>
        <button type="submit" className="btn btn-primary" disabled={adding}>
          {adding ? 'Добавляем…' : 'Добавить'}
        </button>
      </form>
      {addError && <p className="error">{addError}</p>}
      {swapNotice && <p className="empty">{swapNotice}</p>}

      {loading && <p>Загрузка…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && words.length === 0 && (
        <p className="empty">Слов пока нет. Добавьте первое слово!</p>
      )}

      <div className="words-grid">
        {words.map((w) => (
          <WordCard key={w.id} word={w} onDelete={handleDelete} />
        ))}
      </div>
    </Layout>
  );
}