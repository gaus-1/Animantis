import { NavLink, Outlet, useLocation } from 'react-router-dom';

import s from './Layout.module.css';

const NAV_ITEMS = [
  { path: '/', icon: '🏠', label: 'Dashboard' },
  { path: '/agents', icon: '🤖', label: 'Мои агенты' },
  { path: '/create', icon: '✨', label: 'Создать агента' },
  { path: '/map', icon: '🗺️', label: 'Карта мира' },
  { path: '/clans', icon: '⚔️', label: 'Кланы' },
];

function getPageTitle(pathname: string): string {
  const route = NAV_ITEMS.find((item) => item.path === pathname);
  if (route) return route.label;
  if (pathname.startsWith('/agent/')) return 'Профиль агента';
  if (pathname.startsWith('/chat/')) return 'Чат с агентом';
  return 'Animantis';
}

export function Layout() {
  const location = useLocation();
  const title = getPageTitle(location.pathname);

  return (
    <div className={s.layout}>
      {/* Sidebar */}
      <aside className={s.sidebar}>
        <div className={s.sidebarLogo}>
          <img
            src="/assets/logo.svg"
            alt="Animantis"
            className={s.sidebarLogoImg}
          />
          <span className={s.sidebarLogoText}>Animantis</span>
        </div>

        <nav className={s.nav}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${s.navItem} ${isActive ? s.navItemActive : ''}`
              }
              end={item.path === '/'}
            >
              <span className={s.navIcon}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className={s.sidebarFooter}>Animantis v0.1.0</div>
      </aside>

      {/* TopBar */}
      <header className={s.topbar}>
        <h1 className={s.topbarTitle}>{title}</h1>
        <div className={s.topbarActions}>
          <button className={s.topbarBtn} title="Уведомления">
            🔔
          </button>
          <button className={s.topbarBtn} title="Настройки">
            ⚙️
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className={s.main}>
        <Outlet />
      </main>
    </div>
  );
}
