# Mistral Test Results

| Model                              | Quantization | Test Case | Input File | Result |
|------------------------------------|--------------|-----------|------------|--------|
| mistral-small3.2:24b               | Q4 | Table extraction (Oracle 10K Q1) | oracle_10k_2024_q1_small_table.png | ✅ OK |
| ministral-3:14b-instruct-2512-q8_0 | Q8 | Table extraction (Oracle 10K Q1) | oracle_10k_2024_q1_small_table.png | ❌ FAIL |
| mistral-small3.2:24b               | Q4 | Bank statement parsing | bank_statement.png | ✅ OK |
| ministral-3:14b-instruct-2512-q8_0 | Q8 | Bank statement parsing | bank_statement.png | ❌ FAIL |

## Test Details

### Table Extraction Schema
```json
[{"description_text":"str", "price_1":"str or null", "price_2": "str or null"}]
```

### Bank Statement Schema
```json
{"account_number":"int", "statement_date":"str", "period_covered":"str", "total_money_in":"str", "total_money_out":"str", "statement_items":[{"date":"str", "description":"str", "withdrawal":"float or null", "deposit":"float or null", "balance":"float"}]}
```

## Summary
- **mistral-small3.2**: 2/2 tests passed (100%)
- **ministral-3:14b-instruct-2512-q8_0**: 0/2 tests passed (0%)