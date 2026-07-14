import { afterEach, describe, expect, it } from 'vitest';

import { mountForm } from './helpers/mountView.jsx';

const data = {
  model: {
    name: 'sale.order',
    label: { en: 'Orders', es: 'Órdenes' },
    schema: [
      { name: 'name', type: 'string', form: { header: 'title' } },
      {
        name: 'end_date',
        type: 'date',
        label: { en: 'Closing date', es: 'Fecha de cierre' },
        form: {
          leftColumn: 0,
          help: { en: 'Expected closing date', es: 'Fecha probable de cierre' },
        },
      },
      {
        name: 'amount',
        type: 'monetary',
        label: { en: 'Amount', es: 'Importe' },
        form: {
          leftColumn: 1,
          help: { en: 'Taxes included', es: 'Impuestos incluidos' },
        },
      },
    ],
  },
  records: [{ uuid: 'record-1', name: 'SO-001', end_date: '2026-07-01', amount: 100 }],
};

afterEach(() => {
  document.body.innerHTML = '';
});

describe('form contextual help', () => {
  it('opens by click, keeps one help open, and closes outside', async () => {
    const { cleanup } = mountForm(data, 'es');
    const record = document.querySelector('[data-form-record]');
    const helpers = record.querySelectorAll('[data-form-help]');
    const firstTrigger = helpers[0].querySelector('.form-help-trigger');
    const firstPopover = helpers[0].querySelector('.form-help-popover');
    const secondTrigger = helpers[1].querySelector('.form-help-trigger');

    expect(firstPopover.hidden).toBe(true);
    expect(firstTrigger.getAttribute('aria-label')).toContain('Fecha probable de cierre');

    firstTrigger.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(firstPopover.hidden).toBe(false);
    expect(firstTrigger.getAttribute('aria-expanded')).toBe('true');

    secondTrigger.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(firstPopover.hidden).toBe(true);
    expect(secondTrigger.getAttribute('aria-expanded')).toBe('true');

    document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(secondTrigger.getAttribute('aria-expanded')).toBe('false');
    cleanup();
  });

  it('closes with Escape and restores focus to the help button', async () => {
    const { cleanup } = mountForm(data, 'en');
    const trigger = document.querySelector('[data-form-record] .form-help-trigger');

    trigger.click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(trigger);
    cleanup();
  });
});
