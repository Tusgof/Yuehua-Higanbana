# H-A2 / H-L1 Post-Proxy Decision

## Status

- **Date**: 2026-07-06
- **Tracks**: H-A2 Macro-Conditioned ORB Edge, H-L1 LLM News Measurement
- **Evidence tier**: E0 decision/control artifact
- **Decision**: เดิน H-A2 ต่อด้วย local residual/adverse-day analysis ก่อน และยังล็อก H-L1 live LLM/news research ไว้จนกว่าจะมี real timestamp-clean news cases

## Question

หลังจาก H-A2.19 และ L.7 เสร็จแล้ว เราควรทำอะไรต่อโดยไม่หลุดจากสมมติฐาน ไม่ซื้อข้อมูลเพิ่มแบบกว้าง ๆ และไม่เรียก LLM ก่อนมีข่าวจริงที่สะอาดตามเวลา?

## Evidence Review

H-A2.19 เป็น E1 proxy evidence:

| Metric | Value |
|:--|--:|
| Daily rows | 463 |
| Measured 5-minute days | 444 |
| Measured 15-minute days | 444 |
| Existing trade days | 90 |
| Non-risk trade days | 64 |
| Risk-labeled trade days | 26 |
| 5-minute proxy non-risk minus risk | 0.001646 |
| 15-minute proxy non-risk minus risk | 0.000669 |
| Trade PnL non-risk minus risk | 23.375 |
| After big-day trim non-risk minus risk | 8.042741 |

สัญญาณยังมีทิศทางสอดคล้องกัน แต่ยังเป็น `ยังสรุปไม่ได้` เพราะเป็น proxy evidence, ไม่ใช่ exact 2022-10 ORB replay และยัง under-sampled / underpowered สำหรับ E2

L.7 เป็น E1 deterministic baseline:

| Metric | Value |
|:--|--:|
| Macro-only avg trade PnL | -10.56 |
| Clean avg trade PnL | 12.815 |
| Clean minus macro-only avg trade PnL | 23.375 |

ผลนี้ไม่ใช่ LLM/news evidence แต่เป็น baseline ที่ future real-news หรือ LLM scores ต้องชนะให้ได้

## Decision

เลือกทางนี้:

`pre_register_h_a2_residual_adverse_day_analysis`

แปลว่า artifact ถัดไปควรเป็น preregistration สำหรับวิเคราะห์วันที่แพ้หรือวันที่เสี่ยงที่เหลืออยู่ โดยใช้เฉพาะ local artifacts ที่มีแล้ว

## Why

ถ้าเรารีบไปหา 1-minute bars, ซื้อข้อมูล, หรือเปิด live LLM ตอนนี้ เราจะยังไม่ตอบคำถามสำคัญว่า:

> หลังจากตัด macro/VIX risk แล้ว วันที่ยังแพ้เกิดจากอะไร และ H-A2 ควรถูกทำให้แคบลงก่อน exact replay หรือไม่?

การวิเคราะห์นี้ช่วยให้การ chase exact data ในอนาคตมีเหตุผลมากขึ้น และช่วยกันไม่ให้เราเปลี่ยน data source ให้กลายเป็นตัวสมมติฐานเสียเอง

## Allowed Next Work

ทำ preregistration ใหม่สำหรับ H-A2 residual/adverse-day analysis ได้ โดยต้อง:

- ใช้ local artifacts เท่านั้น
- ไม่ใช้ network
- ไม่ใช้ paid data
- ไม่เรียก broker
- ไม่เรียก LLM
- ไม่รัน GDELT live retry
- รายงาน sample counts
- ผูกผลลัพธ์กับคำถามว่าจะ revise, park, หรือ prioritize H-A2 อย่างไร
- คงกฎว่า future H-L1 news/LLM scores ต้องเพิ่มข้อมูลเหนือ deterministic macro/VIX baseline

## Still Forbidden

ยังห้าม:

- claim ว่า H-A2 edge ผ่านแล้ว
- claim ว่า exact 2022-10 ORB replay ถูกทดสอบแล้ว
- claim ว่า L.7 เป็น LLM/news evidence
- live LLM calls
- live GDELT retry ขณะ cooldown ยัง active
- paid data หรือ new provider
- paper trading
- operational validation
- real-money trading

## Verification

```powershell
python scripts\validate_h_a2_h_l1_post_proxy_decision.py
python -m unittest tests.test_validate_h_a2_h_l1_post_proxy_decision
```
