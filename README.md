# BOXX Chatbot Test Automation Suite

Data-driven Python test automation suite for the **BOXX Scam-Detection Chatbot Test API**.

Tests run against the real bot pipeline (isolated from WhatsApp/Meta) via the test API at `https://boxxv2.shunyalabs.ai`.

## Features

- ✅ **Data-driven** — reads test cases from CSV or the existing Excel workbook
- ✅ **Multi-turn** — supports multi-turn conversation flows (e.g. report → classify → recover)
- ✅ **Language-aware** — tests in English, Hindi, Hinglish, and other languages
- ✅ **Flexible column mapping** — adapts to whatever column layout the source sheet uses (no forced rename)
- ✅ **Disclaimer handling** — automatically taps "I Agree" before each test
- ✅ **Analysis assertions** — validates classification, journey, emotion alongside reply text
- ✅ **HTML + CLI report** — shareable `report.html` and plain-text summary table
- ✅ **CI-ready** — env-var config for credentials, exit codes for pipeline integration

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests pytest pytest-html openpyxl pandas
```

### 2. Set environment variables (optional — defaults are present)

```bash
export BOXX_BASE_URL="https://boxxv2.shunyalabs.ai"
export BOXX_API_KEY="boxx-qa-e1ae28770694f29b7ebc2cab3743438a"
```

### 3. Run the tests

**With built-in sample test cases (no sheet file needed):**
```bash
pytest -v
```

**With the existing Excel test case sheet:**
```bash
pytest -v --test-sheet="Docs/Boxx Master Testcases.xlsx"
```

**With HTML report:**
```bash
pytest --html=report.html --self-contained-html -v
```

**Run a single test by ID:**
```bash
pytest -v -k "SAMPLE_001"
# or with real IDs from the sheet:
pytest -v -k "TC_F1_001"
```

**Run smoke tests only:**
```bash
pytest -v -m smoke
```

## Project Structure

```
.
├── boxx_client.py              # API client wrapper (reusable library)
├── test_boxx_scam_flows.py     # Pytest test suite
├── conftest.py                 # Fixtures, hooks, parametrization
├── test_loader.py              # Test case loader (Excel + CSV)
├── pyproject.toml              # Pytest config
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── Docs/
│   └── Boxx Master Testcases.xlsx   # Existing test case workbook
└── comprehensive_test_cases.csv     # Comprehensive generated test cases
```

## Test Case Sheet Format

The loader supports **both CSV and Excel (.xlsx)** with flexible column name detection.

### Excel (recommended for existing sheets)

The loader reads every sheet in the workbook (except Summary & Requirement_Master)
and maps columns by name rather than position. Known column aliases:

| Sheet column name          | Standard key | Purpose                     |
|---------------------------|-------------|-----------------------------|
| `TC ID` / `Test Case`     | `test_id`   | Unique identifier           |
| `Scenario`                | `scenario`   | Test description            |
| `Steps` / `User Input`    | `input`      | User message(s)             |
| `Expected Result`         | `expected`   | Expected bot behaviour      |

Separate multiple turns in a single cell with `|` or newline.

### CSV format

For standalone CSV sheets, use these columns (any order):

```csv
test_id,language,scenario_type,input_message,expected_keywords,expected_classification,expected_journey,notes
TC_001,en,single-turn,I received a phishing SMS,kyc|phishing|link,phishing,,KYC phishing test
TC_002,en,multi-turn,I got a scam call|Yes I paid them|UPI through GPay,recovery|1930|block,upi_fraud,Flow2,Multi-turn UPI fraud
TC_003,hi,single-turn,मेरा पैसा कट गया,upi|recovery,upi_fraud,,Hindi UPI fraud
```

- `input_message` or `input_messages`: user's text. Use `|` to separate multi-turn messages.
- `expected_keywords`: pipe-separated keywords that must all appear in the bot's final reply (case-insensitive).
- `expected_classification`: the scam type the bot should detect (partial match).
- `expected_journey`: the guided flow name (Flow1, Flow2, etc.).
- `scenario_type`: `single-turn` or `multi-turn`.

## API Client (`boxx_client.py`)

Can be imported and reused outside pytest:

```python
from boxx_client import BOXXClient

client = BOXXClient()
session = client.create_session(language="en")
client.agree_to_disclaimer(session)
resp = client.send_message(session, "I got a phishing SMS")
print(resp["reply"])
```

Methods:
- `create_session(language, profile_name) -> str`
- `send_message(session_id, message, button_id, button_title) -> dict`
- `agree_to_disclaimer(session_id) -> dict`
- `get_transcript(session_id) -> list`
- `quick(message, language) -> dict`
- `health_check() -> bool`

## Reporting

### HTML report
```bash
pytest --html=report.html --self-contained-html
```
Open `report.html` in a browser. Each test row shows pass/fail, latency, and errors.

### CLI summary
At the end of every run, a plain-text summary table is printed with test ID, result, language, latency, and scenario.

## CI Integration

The suite exits with standard pytest exit codes:
- `0`: all tests passed
- `1`: some tests failed
- `2`: test execution interrupted

```yaml
# GitHub Actions example
- name: Run BOXX test suite
  run: |
    pip install -r requirements.txt
    pytest -v --html=report.html --self-contained-html
- name: Upload report
  uses: actions/upload-artifact@v4
  with:
    name: boxx-test-report
    path: report.html
```

## Adding New Test Cases

1. **Add rows to the existing Excel** (`Docs/Boxx Master Testcases.xlsx`) — the loader adapts to whatever columns each sheet uses.
2. **Or create a new CSV** and pass it with `--test-sheet`.
3. **Or edit `comprehensive_test_cases.csv`** — the main generated sheet.
