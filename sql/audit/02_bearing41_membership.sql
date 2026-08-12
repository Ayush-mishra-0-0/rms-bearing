/* =========================================================================
   AUDIT 02 - The 41 bearing events: per-loco, per-table membership.
   Reproduces the "which loco was found in which table" grid in the audit
   reports (data_audit_report.md 4.2, comprehensive report 6.2,
   meeting prep 1.1).

   The 41 locos come from the Owner Failure Excel, Failure/Defect column
   filtered to bearing keywords:
       'bear', 'seize', 'labyrinth'
   The artifact owner_rows.txt / owner_failure_classification.csv records
   the full extracted rows; the loco list is frozen below for the DB side.

   Checks for each loco:
     telemetry  = any row in dbo.Lotus_loco_process_signals (indexed, fast)
     faults     = any row in dbo.Lotus_LocoFaultData
     rmslocolist / LomNumber / Loco_Process_Signals_LocoNumber membership
     RMSLocoMap = RMSFlag='Y' entry
   ------------------------------------------------------------------------- */
SELECT
    l.loco,
    CASE WHEN EXISTS (SELECT 1 FROM dbo.Lotus_loco_process_signals t WITH (NOLOCK) WHERE t.locoid = l.loco) THEN 1 ELSE 0 END AS telemetry,
    CASE WHEN EXISTS (SELECT 1 FROM dbo.Lotus_LocoFaultData f WITH (NOLOCK) WHERE f.locoid = l.loco) THEN 1 ELSE 0 END AS faults,
    CASE WHEN EXISTS (SELECT 1 FROM dbo.rmslocolist r WHERE r.locoid = l.loco) THEN 1 ELSE 0 END AS rmslocolist,
    CASE WHEN EXISTS (SELECT 1 FROM dbo.LomNumber n WHERE n.LomNumber = l.loco) THEN 1 ELSE 0 END AS lomnumber,
    CASE WHEN EXISTS (SELECT 1 FROM dbo.Loco_Process_Signals_LocoNumber p WHERE p.LocoNumber = l.loco) THEN 1 ELSE 0 END AS loco_proc_sig_no,
    CASE WHEN EXISTS (SELECT 1 FROM dbo.RMSLocoMap m WHERE m.LomNumber = l.loco AND m.RMSFlag = 'Y') THEN 1 ELSE 0 END AS rmsloco_map
FROM (VALUES
    ('30319'),('30341'),('30354'),('30486'),('30514'),('30532'),('30642'),('30675'),
    ('30751'),('31327'),('32004'),('32054'),('32114'),('32134'),('32515'),('32562'),
    ('33516'),('33574'),('33636'),('33696'),('33700'),('33734'),('37002'),('37038'),
    ('37044'),('37118'),('37271'),('37282'),('37353'),('37361'),('37373'),('37374'),
    ('37491'),('37508'),('37544'),('37619'),('39026'),('39114'),('41733'),('43016'),
    ('43368')
) l(loco)
ORDER BY l.loco;

/* Expected result (verified 31-Jul-2026):
   30514: tel=1 fault=1 rms=0 lom=0 proc=0 map=1
   30532: tel=1 fault=1 rms=0 lom=0 proc=0 map=1
   30751: tel=1 fault=1 rms=1 lom=0 proc=1 map=1
   32134: tel=1 fault=1 rms=0 lom=0 proc=0 map=0
   37282: tel=1 fault=1 rms=1 lom=1 proc=1 map=1
   37361: tel=1 fault=1 rms=0 lom=1 proc=0 map=1
   37044: tel=0 fault=1 rms=0 lom=0 proc=0 map=0
   all 34 others: all zeros.
   => telemetry anywhere: 6 | faults anywhere: 7 | RMSLocoMap fitted: 5
   => zero telemetry anywhere: 35 | in no table at all: 34  */
