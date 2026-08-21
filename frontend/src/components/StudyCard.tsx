// Карточка слова для режима изучения.

import type { WordResponse } from '../types';
import { capitalize } from '../study/study';

interface StudyCardProps {
  word: WordResponse;
}

export default function StudyCard({ word }: StudyCardProps) {
  return (
    <div className="study-card">
      <h2 className="study-word">{capitalize(word.word_en)}</h2>
      {word.transcription && (
        <p className="study-transcription">[{word.transcription}]</p>
      )}
      <p className="study-translation">{word.translation}</p>
    </div>
  );
}