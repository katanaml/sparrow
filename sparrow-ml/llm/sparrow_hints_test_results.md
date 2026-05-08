# Model Comparison: Hints-Driven Document Extraction

## Test Document: Bank Bonds Portfolio (5 positions)
## Hints

| Field | Gemma 4 31B Dense | Qwen 3.6 27B Dense | Mistral Small 3.2 24B |
|---|---|---|---|
| **instrument_name** | ✅ Clean short names | ✅ Clean short names | ❌ Typos (ISHRES), not short enough |
| **valuation** | ✅ European format | ✅ European format | ✅ European format |
| **profit_loss_pct** | ✅ Comma decimal, no % | ✅ Comma decimal, no % | ✅ Comma decimal, no % |
| **risk_category** | ✅ 5/5 correct | ✅ 5/5 correct | ❌ 3/5 (LOW misclassified as MEDIUM) |
| **Overall** | ✅ **Winner** | ✅ **Winner** | ❌ Partial |

## Risk Category Detail

| Position | profit_loss_pct | Expected | Gemma | Qwen | Mistral |
|---|---|---|---|---|---|
| BLACKROCK | -3,02 | LOW | ✅ LOW | ✅ LOW | ❌ MEDIUM |
| ISHARES GOVT BOND | -15,05 | HIGH | ✅ HIGH | ✅ HIGH | ✅ HIGH |
| ISHARES CORP BOND | -3,98 | LOW | ✅ LOW | ✅ LOW | ❌ MEDIUM |
| JP MORGAN | -24,91 | HIGH | ✅ HIGH | ✅ HIGH | ✅ HIGH |
| XTRACKERS HY CORP BOND | -7,61 | MEDIUM | ✅ MEDIUM | ✅ MEDIUM | ✅ MEDIUM |

## Key Takeaway
> Gemma 4 31B and Qwen 3.6 27B handle business rule logic and classification correctly.
> Mistral Small 3.2 24B excels at direct field extraction but struggles with derived classification rules.
> Same hints file — model capability determines the result.