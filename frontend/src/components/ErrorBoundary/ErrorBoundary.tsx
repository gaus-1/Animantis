/**
 * ErrorBoundary — catches React rendering errors and shows a fallback UI.
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

import { Button, Text, Title } from '@mantine/core';

import s from './ErrorBoundary.module.css';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log to console (structlog on backend handles proper logging)
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className={s.errorPage}>
          <div className={s.errorIcon}>⚠️</div>
          <Title order={3}>Что-то пошло не так</Title>
          <Text c="dimmed" size="sm" maw={400}>
            Произошла неожиданная ошибка. Попробуйте обновить страницу
            или вернуться на главную.
          </Text>
          <Button
            color="cyan"
            variant="light"
            onClick={this.handleReset}
            mt="md"
          >
            🏠 На главную
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
