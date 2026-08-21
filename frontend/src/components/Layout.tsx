// Шапка с навигацией, адаптивным меню и кнопкой выхода.

import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const NAV_ITEMS = [
  { to: '/', label: 'Главная' },
  { to: '/words', label: 'Слова' },
  { to: '/study', label: 'Изучение' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'active' : undefined;

  return (
    <div className="layout">
      <header className="header">
        <Link to="/" className="brand">
          Aliaz
        </Link>
        <nav className="nav" aria-label="Основная навигация">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={navLinkClass}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          className="nav-toggle"
          onClick={() => setMenuOpen((o) => !o)}
          aria-expanded={menuOpen}
          aria-label="Открыть меню"
        >
          ☰
        </button>
        <div className="user-area">
          {user && <span className="nickname">{user.nickname}</span>}
          <button type="button" className="btn btn-outline" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      </header>
      {menuOpen && (
        <nav className="nav-mobile" aria-label="Мобильная навигация">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={navLinkClass}
              onClick={() => setMenuOpen(false)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      )}
      <main className="content">{children}</main>
    </div>
  );
}