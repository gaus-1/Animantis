/**
 * API client — единый клиент для всех запросов (из code-style.md).
 *
 * Автоматически прикрепляет X-Telegram-Init-Data header.
 * В dev-режиме работает через Vite proxy → localhost:8080.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

class ApiClient {
  private initData: string | null = null;

  /** Set Telegram initData for authenticated requests. */
  setInitData(data: string): void {
    this.initData = data;
  }

  /** Make an API request and return typed result. */
  async request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> | undefined),
    };

    if (this.initData) {
      headers['X-Telegram-Init-Data'] = this.initData;
    }

    const response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({ detail: 'Network error' }));
      let message = 'Unknown error';
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((e: any) => e.msg).join(', ');
      }
      throw new ApiError(response.status, message);
    }

    return response.json() as Promise<T>;
  }

  /** GET request. */
  async get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }

  /** POST request with JSON body. */
  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /** DELETE request. */
  async del<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' });
  }
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export { ApiError };

export const api = new ApiClient();
