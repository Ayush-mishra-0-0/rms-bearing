/* Phase 1 / Step 7. Classification uses known telemetry bounds only; no telemetry table is read. */
DECLARE @event_date datetime='2025-01-01';
SELECT @event_date event_date,
 CASE WHEN @event_date>='2025-06-02' AND @event_date<'2025-07-31' THEN 'Inside: signals_5 calendar span (daily gaps must still be considered)'
      WHEN @event_date>='2026-05-29' AND @event_date<'2026-05-30' THEN 'Inside: signals_sma one-day span'
      WHEN @event_date>='1929-03-29' AND @event_date<='2025-03-31' THEN 'Unknown: Locoprocessdata has only 94 recording days and no day-level verification here'
      ELSE 'Outside known telemetry period' END AS telemetry_classification;
