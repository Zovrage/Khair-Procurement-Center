import { afterEach, describe, expect, it } from 'vitest';
import { formatDateTime, setDisplayTimeZone } from './client';

afterEach(() => setDisplayTimeZone('Europe/Moscow'));

describe('formatDateTime', () => {
  it('formats timestamps as DD.MM.YYYY HH:mm in the configured timezone', () => {
    setDisplayTimeZone('Europe/Moscow');
    expect(formatDateTime('2026-10-24T10:30:00Z')).toBe('24.10.2026 13:30');
  });

  it('returns an em dash for missing or invalid values', () => {
    expect(formatDateTime(null)).toBe('—');
    expect(formatDateTime('not-a-date')).toBe('—');
  });
});
