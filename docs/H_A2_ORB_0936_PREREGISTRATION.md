# H-A2 ORB เวลา 09:36: Preregistration

## คำถามวิจัย

ภายใต้ prior-close VIX `<25` และไม่มีข่าวมหภาคสำคัญ กลยุทธ์ SPY 0DTE ORB ที่ยืนยันสัญญาณเมื่อแท่งเวลา 09:35 ปิด และเข้าออปชันตั้งแต่ 09:36 สามารถสร้างผลตอบแทนเฉลี่ยหลังต้นทุนเป็นบวกบนข้อมูล OOS ที่ไม่เคยเปิดดูได้หรือไม่

## เหตุผลที่ต้องตั้งคำถามใหม่

checkpoint ก่อนหน้าพบว่าราคาปิดของแท่งที่ประทับเวลา 09:35 รู้ได้จริงเมื่อช่วง 09:35–09:36 สิ้นสุด แต่การ replay เดิมใช้ราคาออปชันเวลา 09:35 จึงเป็นการเข้าเทรดก่อนสัญญาณพร้อมใช้ ตัวเลข PnL จากรอบนั้นใช้ตอบสมมติฐานไม่ได้

การทดลองใหม่นี้จึงเปลี่ยนคำถามอย่างตรงไปตรงมาเป็นการตัดสินใจเวลา 09:36 และล็อก latency 1 นาที ทำให้ snapshot แรกที่ใช้เข้าได้คือ 09:37 การเลือก 1 นาทีเป็นกฎอนุรักษนิยมที่สอดคล้องกับความละเอียดข้อมูล option 1 นาทีและช่วง latency 0/1/2 นาทีที่เคยตรวจใน M5 โดยไม่ได้เลือกค่าจากผล OOS ใหม่

## กฎสัญญาณและเวลา

1. Opening range ใช้แท่งที่ประทับเวลา 09:30–09:34 รวม 5 แท่ง
2. แท่งที่ประทับเวลา 09:35 ครอบคลุมช่วง 09:35–09:36
3. Signal พร้อมใช้เวลา 09:36
4. Order decision ไม่เร็วกว่า 09:36
5. ล็อก execution latency 60 วินาที และใช้ quote สองขาครบชุดครั้งแรกตั้งแต่ 09:37
6. ถ้า quote ไม่ครบให้ข้าม ห้ามสร้างราคา ห้ามย้อนกลับไปใช้ quote เวลา 09:35 หรือ 09:36
7. ทุก trade ต้องผ่าน `signal_available <= decision <= entry_quote` ก่อนเลือก strike หรือคำนวณ PnL

## กฎออปชัน

- ใช้ SPY 0DTE directional debit vertical spread
- Long strike gap เป้าหมาย 1.48 จุด และ spread width 2 จุด
- เลือก strike จริงด้วย `nearest_discrete_strike_rounding` ห้าม interpolation
- เข้าแบบ marketable debit limit โดย cap ที่ long ask ลบ short bid
- Primary implementable PnL ใช้ bid/ask เต็ม ไม่สมมติ price improvement และไม่มี slippage เพิ่มเหนือ displayed spread
- ปิดเวลา 15:45 โดย long bid ลบ short ask
- ค่าธรรมเนียม `$0.64` ต่อขา รวม 4 ขาต่อ round trip

## การแบ่งข้อมูล

- Artifact ที่เห็นผลถึง 2026-04-24 เป็น development/diagnostic evidence
- Fresh validation ต้องอยู่หลัง 2026-04-24 ตามลำดับเวลา
- ห้าม random split, OOS tuning, threshold search หรือเลือก latency ที่ให้ผลดีที่สุด
- 20 วันที่เปิดดูใน checkpoint ก่อนหน้าใช้ได้เฉพาะ fixture และ diagnostic ห้ามนับเป็น fresh OOS

## Regime ที่ต้องรายงาน

- Low VIX: prior-close VIX `<15`
- Normal VIX: `15 <= prior-close VIX <25`
- ห้าม trade เมื่อ prior-close VIX `>=25`
- ห้าม trade ในวัน high-importance macro event
- Trend ใช้ prior trading-day SPY close เทียบ SMA20 ที่คำนวณถึงวันก่อนหน้าเท่านั้น ห้ามใช้ราคาวันเป้าหมาย

## เกณฑ์สถิติ

ต้องรายงาน mean/total implementable PnL, Sharpe, PSR, MinTRL, DSR, ES95, ES99, worst-day loss และ big-day dependency ค่า MinTRL ที่แม่นยำยังคำนวณล่วงหน้าไม่ได้ เพราะต้องใช้ distribution ของ return ที่ timestamp ถูกต้อง หากจำนวนจริงต่ำกว่า MinTRL ให้ติดป้าย `under-sampled` และสรุป `ยังสรุปไม่ได้`

DSR ต้องนับอย่างน้อย 10 trials: 9 trials ที่สืบทอดจาก M5.5 และกฎ 09:36 ใหม่ 1 trial ห้ามอ้างว่าเป็น single-trial research เพื่อละเว้น multiple-testing adjustment

## ข้อห้ามของรอบนี้

- ไม่รันการทดลองและไม่เปิดดู target-day PnL
- ไม่ซื้อข้อมูลหรือเรียก live metadata API
- ไม่เรียก LLM และไม่ส่ง broker order
- ไม่อนุมัติ paper trading, E2, operational validation หรือเงินจริง
- ไม่เขียน research log เพราะยังไม่มีผลทดลองใหม่

แหล่งอ้างอิงหลักมาจาก local LLM Wiki: Backtest Validation Protocol, Lookahead Leakage, SPY 0DTE Opening Range Breakout, Implementable Option PNL, MinTRL, PSR และ DSR โดย SHA-256 ถูกล็อกใน JSON preregistration
