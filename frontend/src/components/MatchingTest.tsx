// Тест сопоставления: выбор русского перевода для английского слова.

import { useState } from 'react';
import type { WordResponse } from '../types';
import { buildOptions, capitalize } from '../study/study';

interface MatchingTestProps {
  words: WordResponse[];
  onRestart: () => void;
  onHome: () => void;
}

export default function MatchingTest({ words, onRestart, onHome }: MatchingTestProps) {
  const [current, setCurrent] = useState(0);
  const [score, setScore] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [finished, setFinished] = useState(false);

  const word = words[current];
  const options = buildOptions(word, words);

  const handleSelect = (option: string) => {
    if (selected !== null) return;
    setSelected(option);
    if (option === word.translation) {
      setScore((s) => s + 1);
    }
  };

  const handleNext = () => {
    if (current + 1 >= words.length) {
      setFinished(true);
    } else {
      setCurrent((c) => c + 1);
      setSelected(null);
    }
  };

  if (finished) {
    return (
      <div className="study-result">
        <h2>Результат</h2>
        <p className="study-score">
          Правильно: {score} из {words.length}
        </p>
        <div className="study-actions">
          <button type="button" className="btn btn-primary" onClick={onRestart}>
            Пройти ещё раз
          </button>
          <button type="button" className="btn btn-outline" onClick={onHome}>
            На главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="study-test">
      <p className="study-progress">
        Вопрос {current + 1} из {words.length}
      </p>
      <h2 className="study-word">{capitalize(word.word_en)}</h2>
      <p className="study-hint">Выберите правильный перевод</p>
      <div className="study-options">
        {options.map((option) => {
          let className = 'study-option';
          if (selected !== null) {
            if (option === word.translation) {
              className += ' correct';
            } else if (option === selected) {
              className += ' wrong';
            }
          }
          return (
            <button
              key={option}
              type="button"
              className={className}
              onClick={() => handleSelect(option)}
              disabled={selected !== null}
            >
              {option}
            </button>
          );
        })}
      </div>
      {selected !== null && (
        <button type="button" className="btn btn-primary" onClick={handleNext}>
          {current + 1 >= words.length ? 'Показать результат' : 'Далее'}
        </button>
      )}
    </div>
  );
}