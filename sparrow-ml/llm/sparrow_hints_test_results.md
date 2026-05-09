# Model Comparison: Hints-Driven Document Extraction

## Test Document: Bank Bonds Portfolio (5 positions)
## Hints: instrument_name | valuation | profit_loss_pct | risk_category

| Field | Gemma 4 31B Dense | Qwen 3.6 27B Dense | Ministral 3 14B |
|---|---|---|---|
| **instrument_name** | ✅ Clean short names | ✅ Clean short names | ❌ Typos (ISHERES, XTRAKERS) |
| **valuation** | ✅ European format | ✅ European format | ✅ European format |
| **profit_loss_pct** | ✅ Comma decimal, no % | ✅ Comma decimal, no % | ✅ Comma decimal, no % |
| **risk_category** | ✅ 5/5 correct | ✅ 5/5 correct | ✅ 5/5 correct |
| **Overall** | ✅ **Winner** | ✅ **Winner** | ⚠️ Partial |

## Risk Category Detail

| Position | profit_loss_pct | Expected | Gemma | Qwen | Ministral |
|---|---|---|---|---|---|
| BLACKROCK | -3,02 | LOW | ✅ LOW | ✅ LOW | ✅ LOW |
| ISHARES GOVT BOND | -15,05 | HIGH | ✅ HIGH | ✅ HIGH | ✅ HIGH |
| ISHARES CORP BOND | -3,98 | LOW | ✅ LOW | ✅ LOW | ✅ LOW |
| JP MORGAN | -24,91 | HIGH | ✅ HIGH | ✅ HIGH | ✅ HIGH |
| XTRACKERS HY CORP BOND | -7,61 | MEDIUM | ✅ MEDIUM | ✅ MEDIUM | ✅ MEDIUM |

## Key Takeaway
> Gemma 4 31B and Qwen 3.6 27B handle business rule logic, classification and instrument name extraction correctly.
> Ministral 3 14B handles classification rules correctly but has consistent OCR/spelling errors on instrument names (ISHERES, XTRAKERS).
> Same hints file — model capability determines the result.