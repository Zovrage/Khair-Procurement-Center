export type Role = 'admin' | 'buyer' | 'manager';

export interface UserProfile {
  id: string;
  username: string;
  full_name: string;
  role: Role;
}

export interface Factory {
  id: string;
  name: string;
  short_name?: string | null;
  contact_person?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  email?: string | null;
  website?: string | null;
  address?: string | null;
  products?: string | null;
  default_dispatch_method?: string | null;
  payment_terms?: string | null;
  production_lead_time_days?: number | null;
  comment?: string | null;
  status: 'active' | 'archived';
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProcurementRequest {
  id: string;
  bitrix_deal_id: string;
  bitrix_title: string;
  bitrix_url?: string | null;
  bitrix_category_id?: string | null;
  bitrix_stage_id?: string | null;
  bitrix_responsible_id?: string | null;
  bitrix_created_at?: string | null;
  factories_count: number;
  last_dispatch?: string | null;
  procurement_complete: boolean;
}

export interface OrderNumber {
  id: string;
  request_factory_id: string;
  order_number: string;
  created_at: string;
  updated_at: string;
}

export interface RequestFactory {
  id: string;
  procurement_request_id: string;
  factory_id: string;
  factory_name?: string | null;
  dispatch_datetime?: string | null;
  dispatch_method?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  created_at: string;
  updated_at: string;
  order_numbers: string[];
  order_number_records: OrderNumber[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';
let displayTimeZone = 'Europe/Moscow';

export function setDisplayTimeZone(timeZone: string) {
  displayTimeZone = timeZone;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (typeof document !== 'undefined' && init.method && !['GET', 'HEAD', 'OPTIONS'].includes(init.method.toUpperCase())) {
    const csrfCookie = document.cookie.split('; ').find((cookie) => cookie.startsWith('khair_csrf='))?.split('=').slice(1).join('=');
    if (csrfCookie) headers.set('X-CSRF-Token', decodeURIComponent(csrfCookie));
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers, credentials: 'same-origin' });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Ошибка запроса (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function formatDateTime(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  const dateText = new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: displayTimeZone,
  }).format(date);
  const timeText = new Intl.DateTimeFormat('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone: displayTimeZone,
  }).format(date);
  return `${dateText} ${timeText}`;
}
