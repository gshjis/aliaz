// Главная страница: приветствие и карточки-кнопки для разделов.

import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useAuthStore } from '../store/authStore';

interface HomeCardData {
  icon: string;
  title: string;
  description: string;
  href?: string;
  disabled?: boolean;
}

const CARDS: HomeCardData[] = [
  {
    icon: '➕',
    title: 'Добавить слова',
    description: 'Добавляйте новые слова и переводы',
    href: '/words',
  },
  {
    icon: '🎴',
    title: 'Изучить слова',
    description: 'Карточки и тест на сопоставление',
    href: '/study',
  },
  {
    icon: '🎧',
    title: 'Аудирование',
    description: 'Слушайте и понимайте на слух',
    disabled: true,
  },
  {
    icon: '🗣',
    title: 'Говорение',
    description: 'Тренируйте произношение',
    disabled: true,
  },
  {
    icon: '📖',
    title: 'Чтение',
    description: 'Читайте и переводите тексты',
    disabled: true,
  },
];

export default function HomePage() {
  const user = useAuthStore((s) => s.user);
  const nickname = user?.nickname ?? 'друг';

  return (
    <Layout>
      <h2 className="home-title">Привет, {nickname}!</h2>
      <p className="home-subtitle">Чем займёмся сегодня?</p>

      <div className="home-grid">
        {CARDS.map((card) =>
          card.disabled ? (
            <div
              key={card.title}
              className="home-card-disabled"
              aria-disabled="true"
            >
              <span className="home-card-icon" aria-hidden="true">
                {card.icon}
              </span>
              <h3 className="home-card-title">{card.title}</h3>
              <p className="home-card-desc">{card.description}</p>
              <span className="badge">Скоро</span>
            </div>
          ) : (
            <Link
              key={card.title}
              to={card.href!}
              className="home-card"
              aria-label={card.title}
            >
              <span className="home-card-icon" aria-hidden="true">
                {card.icon}
              </span>
              <h3 className="home-card-title">{card.title}</h3>
              <p className="home-card-desc">{card.description}</p>
            </Link>
          ),
        )}
      </div>
    </Layout>
  );
}