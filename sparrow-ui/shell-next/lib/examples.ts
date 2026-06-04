// Sample JSON results for example documents
// Equivalent of bonds_json, lab_results_json, bank_statement_json in Gradio app.py

export const BONDS_JSON = {
  data: [
    { instrument_name: "UNITS BLACKROCK FIX INC DUB FDS PLC ISHS EUR INV GRD CP BD IDX/INST/E", valuation: 19049 },
    { instrument_name: "UNITS ISHARES III PLC CORE EUR GOVT BOND UCITS ETF/EUR", valuation: 83488 },
    { instrument_name: "UNITS ISHARES III PLC EUR CORP BOND 1-5YR UCITS ETF/EUR", valuation: 213030 },
    { instrument_name: "UNIT ISHARES VI PLC/JP MORGAN USD E BOND EUR HED UCITS ETF DIST/HDGD/", valuation: 32774 },
    { instrument_name: "UNITS XTRACKERS II SICAV/EUR HY CORP BOND UCITS ETF/-1D-/DISTR.", valuation: 23643 },
  ],
  valid: "true",
};

export const LAB_RESULTS_JSON = {
  patient_name: "Yash M. Patel",
  patient_age: "21 Years",
  patient_pid: 555,
  lab_results: [
    { investigation: "Hemoglobin (Hb)",                              result: 12.5,   reference_value: "13.0 - 17.0",   unit: "g/dL"      },
    { investigation: "Total RBC count",                              result: 5.2,    reference_value: "4.5 - 5.5",     unit: "mill/cumm" },
    { investigation: "Packed Cell Volume (PCV)",                     result: 57.5,   reference_value: "40 - 50",        unit: "%"         },
    { investigation: "Mean Corpuscular Volume (MCV)",                result: 87.75,  reference_value: "83 - 101",       unit: "fL"        },
    { investigation: "Mean Corpuscular Hemoglobin (MCH)",            result: 27.2,   reference_value: "27 - 32",        unit: "pg"        },
    { investigation: "Mean Corpuscular Hemoglobin Concentration (MCHC)", result: 32.8, reference_value: "32.5 - 34.5", unit: "g/dL"      },
    { investigation: "Red Cell Distribution Width (RDW)",            result: 13.6,   reference_value: "11.6 - 14.0",   unit: "%"         },
    { investigation: "Total WBC count",                              result: 9000,   reference_value: "4000-11000",     unit: "cumm"      },
    { investigation: "Neutrophils",                                  result: 60,     reference_value: "50 - 62",        unit: "%"         },
    { investigation: "Lymphocytes",                                  result: 31,     reference_value: "20 - 40",        unit: "%"         },
    { investigation: "Eosinophils",                                  result: 1,      reference_value: "00 - 06",        unit: "%"         },
    { investigation: "Monocytes",                                    result: 7,      reference_value: "00 - 10",        unit: "%"         },
    { investigation: "Basophils",                                    result: 1,      reference_value: "00 - 02",        unit: "%"         },
    { investigation: "Absolute Neutrophils",                         result: 6000,   reference_value: "1500 - 7500",   unit: "cells/mcL" },
    { investigation: "Absolute Lymphocytes",                         result: 3100,   reference_value: "1300 - 3500",   unit: "cells/mcL" },
    { investigation: "Absolute Eosinophils",                         result: 100,    reference_value: "00 - 500",       unit: "cells/mcL" },
    { investigation: "Absolute Monocytes",                           result: 700,    reference_value: "200 - 950",      unit: "cells/mcL" },
    { investigation: "Absolute Basophils",                           result: 100,    reference_value: "00 - 300",       unit: "cells/mcL" },
    { investigation: "Platelet Count",                               result: 320000, reference_value: "150000 - 410000", unit: "cumm"     },
  ],
  valid: "true",
};

export const BANK_STATEMENT_JSON = {
  items: [
    { Date: "02/01", Description: "PGD EasyPay Debit",                  Withdrawal: "203.24",   Deposit: "",        Balance: "22,098.23" },
    { Date: "02/02", Description: "AB&B Online Payment*****",            Withdrawal: "71.23",    Deposit: "",        Balance: "22,027.00" },
    { Date: "02/04", Description: "Check No. 2345",                      Withdrawal: "",         Deposit: "450.00",  Balance: "22,477.00" },
    { Date: "02/05", Description: "Payroll Direct Dep 23422342 Giants",  Withdrawal: "",         Deposit: "2,534.65",Balance: "25,011.65" },
    { Date: "02/06", Description: "Signature POS Debit - TJP",           Withdrawal: "84.50",    Deposit: "",        Balance: "24,927.15" },
    { Date: "02/07", Description: "Check No. 234",                       Withdrawal: "1,400.00", Deposit: "",        Balance: "23,527.15" },
    { Date: "02/08", Description: "Check No. 342",                       Withdrawal: "",         Deposit: "25.00",   Balance: "23,552.15" },
    { Date: "02/09", Description: "FPB AutoPay**** Credit Card",         Withdrawal: "456.02",   Deposit: "",        Balance: "23,096.13" },
    { Date: "02/08", Description: "Check No. 123",                       Withdrawal: "",         Deposit: "25.00",   Balance: "23,552.15" },
    { Date: "02/09", Description: "FPB AutoPay**** Credit Card",         Withdrawal: "156.02",   Deposit: "",        Balance: "23,096.13" },
    { Date: "02/08", Description: "Cash Deposit",                        Withdrawal: "",         Deposit: "25.00",   Balance: "23,552.15" },
  ],
};

export type ExampleId = "bonds_table.png" | "lab_results.png" | "bank_statement.png";

export const EXAMPLE_DATA: Record<ExampleId, {
  json: unknown;
  query: string;
  schema: string;
}> = {
  "bonds_table.png": {
    json: BONDS_JSON,
    query: JSON.stringify([{ instrument_name: "str", valuation: 0 }]),
    schema: `[\n  {\n    "instrument_name": "str",\n    "valuation": "int"\n  }\n]`,
  },
  "lab_results.png": {
    json: LAB_RESULTS_JSON,
    query: JSON.stringify({ patient_name: "str", patient_age: "str", patient_pid: "int", lab_results: [{ investigation: "str", result: "float", reference_value: "str", unit: "str" }] }),
    schema: `{\n  "patient_name": "str",\n  "patient_age": "str",\n  "patient_pid": "int",\n  "lab_results": [{\n    "investigation": "str",\n    "result": "float",\n    "reference_value": "str",\n    "unit": "str"\n  }]\n}`,
  },
  "bank_statement.png": {
    json: BANK_STATEMENT_JSON,
    query: "*",
    schema: "*",
  },
};