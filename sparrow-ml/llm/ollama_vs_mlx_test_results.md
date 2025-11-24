# OLLAMA vs MLX-VLM Test Results

## Test Results Summary

| Model                                                           | Framework | Bonds Table | Financial Statement | Invoice | Bank Statement |
|-----------------------------------------------------------------|-----------|-------------|---------------------|---------|----------------|
| qwen3-vl:30b-a3b-instruct-q8_0                                  | Ollama | ✅ OK | ✅ OK | ✅ OK | ✅ OK |
| mistral-small3.2 24b q4                                         | Ollama | ✅ OK | ✅ OK | ✅ OK | ✅ OK |
| mlx-community/Qwen3-VL-30B-A3B-Instruct-8bit                    | MLX | ✅ OK | ❌ FAIL | ✅ OK | ❌ FAIL |
| lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-MLX-8bit | MLX | ✅ OK | ❌ FAIL | ✅ OK | ❌ FAIL |

## Test Files

- **Bonds Table**: `bonds_table.png`
- **Financial Statement**: `oracle_10k_2024_q1_small_table.png`
- **Invoice**: `invoice_1.jpg`
- **Bank Statement**: `bank_statement.png`

## Summary

- **Best Overall Performance**: qwen3-vl:30b-a3b-instruct-q8_0, mistral-small3.2, and mistral-small3.2:24b-instruct-2506-q8_0 (all Ollama) - passed all tests
- **MLX Models**: Both MLX models failed on Financial Statement and Bank Statement tests
