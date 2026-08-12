/* Candidate health fields only; no labels are created here. */
SELECT TOP (1000) locoid,devicetime,xtempmotor1_1,xtempmotor2_1,xtempmotor3_1,xspeedloco,xvist_a1_1,xvist_a2_1,xvist_a3_1 FROM dbo.Locoprocessdata ORDER BY devicetime DESC;
