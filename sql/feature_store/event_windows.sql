/* Event-window manifest; read-only. */
DECLARE @failure datetime='2026-06-08'; SELECT DATEADD(day,-30,@failure) window_start,DATEADD(day,-14,@failure) fourteen_day_start,DATEADD(day,-7,@failure) seven_day_start,@failure failure_time;
