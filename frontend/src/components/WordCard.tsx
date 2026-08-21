// Карточка слова с переводом, транскрипцией и исправленным словом.

import type { WordResponse } from '../types';

interface WordCardProps {
  word: WordResponse;
  onDelete: (id: number) => void;
}

export default function WordCard({ word, onDelete }: WordCardProps) {
  return (
    <div className="word-card">
      <div className="word-card-head">
        <h3 className="word-en">{word.word_en}</h3>
        <button
          type="button"
          className="btn btn-danger"
          onClick={() => onDelete(word.id)}
          aria-label={`Удалить слово ${word.word_en}`}
        >
          Удалить
        </button>
      </div>
      {word.transcription && <p className="word-transcription">[{word.transcription}]</p>}
      <p className="word-translation">{word.translation}</p>
      {word.corrected_word && word.corrected_word !== word.word_en && (
        <p className="word-corrected">
          Исправлено: <strong>{word.corrected_word}</strong>
        </p>
      )}
    </div>
  );
}