/**
 * Layout — main application shell with responsive sidebar and mobile bottom nav.
 *
 * Uses Mantine AppShell for structure:
 * - Desktop: fixed sidebar (260px) + top header
 * - Tablet: collapsible sidebar via burger menu
 * - Mobile: bottom navigation bar, no sidebar
 */

import { useCallback } from 'react';

import {
  AppShell,
  Burger,
  Group,
  Text,
  UnstyledButton,
} from '@mantine/core';
import { useDisclosure, useMediaQuery } from '@mantine/hooks';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';
import { useWebSocket } from '@/hooks/useWebSocket';

import s from './Layout.module.css';

/* ── Navigation items ──────────────────────────────────────── */

interface NavItem {
  path: string;
  icon: string;
  label: string;
  shortLabel: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/', icon: '🏠', label: 'Dashboard', shortLabel: 'Home' },
  { path: '/create', icon: '✨', label: 'Создать агента', shortLabel: 'Создать' },
  { path: '/map', icon: '🗺️', label: 'Карта мира', shortLabel: 'Карта' },
  { path: '/feed', icon: '📰', label: 'Лента', shortLabel: 'Лента' },
  { path: '/clans', icon: '⚔️', label: 'Кланы', shortLabel: 'Кланы' },
];

function getPageTitle(pathname: string): string {
  const route = NAV_ITEMS.find((item) => item.path === pathname);
  if (route) return route.label;
  if (pathname.startsWith('/agent/')) return 'Профиль агента';
  if (pathname.startsWith('/chat/')) return 'Чат с агентом';
  if (pathname === '/settings') return 'Настройки';
  if (pathname === '/agents') return 'Мои агенты';
  return 'Animantis';
}

/* ── Component ─────────────────────────────────────────────── */

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { userId, isAuthenticated } = useAuth();
  const { connected: wsConnected } = useWebSocket(userId);
  const title = getPageTitle(location.pathname);
  const [sidebarOpened, { toggle: toggleSidebar, close: closeSidebar }] = useDisclosure(false);
  const isMobile = useMediaQuery('(max-width: 768px)');

  const handleNavClick = useCallback((path: string) => {
    navigate(path);
    closeSidebar();
  }, [navigate, closeSidebar]);

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 260,
        breakpoint: 'sm',
        collapsed: { mobile: !sidebarOpened },
      }}
      padding="md"
      classNames={{
        root: s.shell,
        header: s.header,
        navbar: s.navbar,
        main: s.main,
      }}
    >
      {/* ── Header ──────────────────────────────────────────── */}
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="sm">
            {!isMobile ? null : (
              <Burger
                opened={sidebarOpened}
                onClick={toggleSidebar}
                size="sm"
                color="var(--text-secondary)"
              />
            )}
            <img
              src="/assets/logo.png"
              alt="Animantis"
              className={s.headerLogo}
            />
            <Text fw={700} size="lg" className={s.headerTitle}>
              {title}
            </Text>
          </Group>
          {isAuthenticated && (
            <Group gap="xs">
              <UnstyledButton
                className={s.headerBtn}
                title="Уведомления"
              >
                🔔
              </UnstyledButton>
              <UnstyledButton
                className={s.headerBtn}
                title="Настройки"
                onClick={() => handleNavClick('/settings')}
              >
                ⚙️
              </UnstyledButton>
            </Group>
          )}
        </Group>
      </AppShell.Header>

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <AppShell.Navbar>
        <div className={s.navbarLogo}>
          <img
            src="/assets/logo.png"
            alt="Animantis"
            className={s.logoImg}
          />
          <span className={s.logoText}>Animantis</span>
        </div>

        <nav className={s.nav}>
          {NAV_ITEMS.map((item) => {
            if (!isAuthenticated && ['/', '/create'].includes(item.path)) return null;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                `${s.navItem} ${isActive ? s.navItemActive : ''}`
              }
              end={item.path === '/'}
              onClick={closeSidebar}
            >
              <span className={s.navIcon}>{item.icon}</span>
              {item.label}
            </NavLink>
            );
          })}
        </nav>

        <div className={s.navbarFooter}>
          <span className={wsConnected ? s.statusDotOnline : s.statusDot} />
          {wsConnected ? 'Online' : 'Offline'} · v0.2.0
        </div>
      </AppShell.Navbar>

      {/* ── Main content ────────────────────────────────────── */}
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>

      {/* ── Mobile bottom navigation ────────────────────────── */}
      {isMobile && (
        <div className={s.bottomNav}>
          {NAV_ITEMS.map((item) => {
            if (!isAuthenticated && ['/', '/create'].includes(item.path)) return null;
            const isActive = item.path === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.path);
            return (
              <button
                key={item.path}
                type="button"
                className={`${s.bottomNavItem} ${isActive ? s.bottomNavItemActive : ''}`}
                onClick={() => handleNavClick(item.path)}
              >
                <span className={s.bottomNavIcon}>{item.icon}</span>
                <span className={s.bottomNavLabel}>{item.shortLabel}</span>
              </button>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
