# BOXX Chatbot Test Automation Guide

> **Complete documentation** — what, why, and how we test the BOXX scam-detection chatbot.

---

## Table of Contents

1. [What We Are Testing](#1-what-we-are-testing)
2. [The Big Picture: Test Architecture](#2-the-big-picture-test-architecture)
3. [Understanding the API](#3-understanding-the-api)
4. [Module-by-Module Breakdown](#4-module-by-module-breakdown)
5. [How Test Execution Works](#5-how-test-execution-works)
6. [Test Case Coverage](#6-test-case-coverage)
7. [Commands Cheat Sheet](#7-commands-cheat-sheet)
8. [What We Expect From the Bot](#8-what-we-expect-from-the-bot)
9. [Interpreting Failures](#9-interpreting-failures)
10. [Adding New Test Cases](#10-adding-new-test-cases)
11. [CI/CD Integration](#11-cicd-integration)
12. [Test Case Inventory](#12-test-case-inventory)

---

## 1. What We Are Testing

We are testing **BOXX**, an AI-powered WhatsApp chatbot that helps Indian users:

- **Detect** if a message, call, or situation is a scam or fraud
- **Classify** the type of scam (phishing, OTP fraud, UPI fraud, digital arrest, etc.)
- **Route** the user into the correct guided flow (Flow1 → Flow2 for recovery, Flow4 for prevention, etc.)
- **Provide** actionable steps (call 1930, block accounts, file FIR, reset passwords)
- **Handle** multiple languages: English, Hindi, and Hinglish (mixed Hindi-English)
- **Emotionally support** distressed users while guiding them to action
- **Log and save** every test result with full API response data into timestamped CSV files for analysis

### What We Do NOT Test

- WhatsApp/Meta integration — the test API runs the **same bot pipeline** but bypasses WhatsApp
- Real monetary transactions — all sessions are simulated
- Load/performance — latency is tracked but the test suite does not performance-test
- Unit tests of internal components — we test end-to-end through the API

---

## 2. The Big Picture: Test Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        pytest test runner                               │
│                                                                         │
│  ┌──────────────┐    ┌─────────────────────┐    ┌────────────────────┐  │
│  │  conftest.py  │    │ test_boxx_scam_     │    │  test_loader.py    │  │
│  │  (fixtures &  │───▶│ flows.py            │◀───│  (reads Excel/CSV, │  │
│  │   hooks)      │    │ (parametrized       │    │   auto-detects     │  │
│  │               │    │  test cases)        │    │   column layout)   │  │
│  └──────┬────────┘    └────────┬────────────┘    └────────────────────┘  │
│         │                      │                                         │
│         │              ┌───────▼────────┐                               │
│         │              │ boxx_client.py │                               │
│         │              │ (API client    │                               │
│         │              │  wrapper)      │                               │
│         │              └───────┬────────┘                               │
│         │                      │                                         │
│         │              ┌───────▼────────┐                               │
│         └──────────────▶  Live BOXX API  │                               │
│                    ┌───▶ boxxv2.         │                               │
│                    │    shunyalabs.ai    │                               │
│                    │   (isolated test   │                               │
│                    │    environment —   │                               │
│                    │    no WhatsApp)    │                               │
│                    │                    │                               │
│                    └────────────────────┘                               │
│                                                                         │
│  Test Data Sources:                                                     │
│  ┌──────────────┐  ┌─────────────────────┐  ┌──────────────────────┐   │
│  │ 8 Sample     │  │ comprehensive_test_ │  │  Boxx Master         │   │
│  │ Cases        │  │ cases.csv           │  │  Testcases.xlsx      │   │
│  │ (built-in)   │  │ (558 cases, 64      │  │ (513 cases across    │   │
│  │              │  │  categories)        │  │  18 existing sheets) │   │
│  └──────────────┘  └─────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flow for One Test Case

```
1. Health Check ───▶ GET /api/test/health (once per session)
                           │
2. Create Session ──▶ POST /api/test/session (fresh session, set language)
                           │
3. Disclaimer ─────▶ POST .../session/{id}/message
                     { button_id: "agree_disclaimer" }
                           │
4. Send Message(1) ─▶ POST .../session/{id}/message
                     { message: "I got a KYC phishing SMS" }
                           │
5. Assertions ──────▶ • Reply is non-empty
                      • At least 1 expected keyword found in reply
                      • classification (if specified) matches
                      • journey (if specified) matches
                           │
6. Loop for more ───▶ Repeat steps 4-5 for each turn in multi-turn test
```

---

## 3. Understanding the API

All test cases communicate with the BOXX Test API. Here's what every endpoint does:

### `GET /api/test/health`
**Ping the service.** Called once at suite start. If this fails, the entire run aborts immediately with a clear message.

### `POST /api/test/session`
**Create a new, isolated conversation.** Think of this as a fresh WhatsApp chat. Every test gets its own session — never reuse sessions.

```json
Request:  { "language": "en", "profile_name": "QA Bot", "phone": "simulation" }
Response: { "status": "success", "data": { "session_id": "abc-123" } }
```

### `POST /api/test/session/{id}/message`
**Send one user message, get the bot's reply.** This is the core endpoint.

```json
Request:  { "message": "I got an SMS saying my KYC will expire" }
Response: {
  "status": "success",
  "data": {
    "reply": "Based on what you shared, this appears to be a *Phishing Scam*.",
    "replies": [...],
    "reply_count": 1,
    "latency_ms": 5432,
    "analysis": {
      "classification": "phishing",
      "journey": "check_scam",
      "emotion": "panic",
      "emotion_language": "en",
      "loss_assessment": "no_loss"
    }
  }
}
```

Key response fields:
- **`reply`** — all bubbles joined (simplest to assert on)
- **`replies`** — individual bubbles the bot sent
- **`analysis.classification`** — the scam type the bot detected (may be empty on first turn if bot asks intake questions first)
- **`analysis.journey`** — which guided flow the bot routed to
- **`latency_ms`** — how long the bot took (monitored, not asserted)

### `POST /api/test/session/{id}/message` (Button)
To simulate tapping a WhatsApp button:
```json
{ "button_id": "agree_disclaimer", "button_title": "I Agree" }
```

### `GET /api/test/session/{id}`
**Fetch the full transcript** — useful for debugging failed assertions.

### `POST /api/test/quick`
**One-shot convenience** — creates a session and sends one message. Good for health checks.

### Important Behavioral Notes

1. **Disclaimer first turn:** A fresh session's first real turn returns a short disclaimer asking the user to tap "I Agree." All tests send this button automatically — you never see it in the assertions.

2. **Intake question:** After the disclaimer, the bot often asks "Is this happening to you, or to a family member?" before classifying the scam. This is by design — the bot doesn't always classify on the first real turn. Our test assertions handle this gracefully by:
   - Using **ANY-match** for keywords (only one keyword needs to match)
   - **Warning** instead of failing when classification is expected but the bot asked an intake question instead

3. **State persists** within a session — context, language, emotion, and classification carry across turns, exactly like a real chat.

4. **Errors:** Non-2xx responses return `{"status": "error", "message": "..."}`. The client raises `BOXXError` on these — never silent failures.

---

## 4. Module-by-Module Breakdown

### `boxx_client.py` — The API Client

**Purpose:** Thin, reusable HTTP wrapper around all 6 API endpoints.

**How it works:**
- Configurable via `BOXX_BASE_URL` and `BOXX_API_KEY` environment variables (or hardcoded defaults)
- Persistent `requests.Session` with headers pre-set
- 45-second timeout on all requests (bot turns can take 2–9 seconds hitting the LLM pipeline)
- Raises `BOXXError` on any non-2xx response or connection failure
- Logs every request at debug level, errors at warning level

**Methods:**
| Method | API Call | Returns |
|--------|----------|---------|
| `health_check()` | `GET /api/test/health` | `bool` |
| `create_session(language, profile_name)` | `POST /api/test/session` | `str` (session_id) |
| `send_message(session_id, message, button_id, button_title)` | `POST .../message` | `dict` (response data) |
| `agree_to_disclaimer(session_id)` | Convenience for button call | `dict` |
| `get_transcript(session_id)` | `GET .../session/{id}` | `list` |
| `quick(message, language)` | `POST /api/test/quick` | `dict` |

**Usage outside pytest:**
```python
from boxx_client import BOXXClient

client = BOXXClient()
session = client.create_session(language="hing")
resp = client.send_message(session, "Maine OTP bata diya")
print(resp["reply"])
```

---

### `test_loader.py` — The Test Case Loader

**Purpose:** Reads test cases from Excel (.xlsx) or CSV files and converts them to `TestCase` dataclass instances.

**How it works:**

**For Excel files:**
1. Opens every sheet except `Summary` and `Requirement_Master`
2. Reads the header row (row 1) and maps column names to standard keys using fuzzy matching
3. For each data row:
   - Extracts `test_id`, scenario description, user input, expected result
   - Detects scam type from the expected result text using keyword heuristics
   - Splits pipe-separated (`|`) or newline-separated inputs into multi-turn flows
   - Guesses language (`hi` if Devanagari characters found, `en` otherwise)
4. Deduplicates by `test_id`

**For CSV files:**
- Standard `csv.DictReader` with column names matching exactly what's in the header row

**Column Name Mapping (Excel):**
The loader auto-detects columns regardless of what they're named:

| Found in sheet → | Mapped to |
|---|---|
| `TC ID`, `Test Case`, `Test ID`, `test_id` | `test_id` |
| `Scenario` | `scenario` |
| `User Input`, `Steps`, `User Query`, `Step`, `Precondition`, `Input Message` | `input` |
| `Expected Result`, `Expected Platform Response`, `Expected Bot Behaviour`, `Expected AI Behaviour` | `expected` |
| `Expected Detection` | `expected_detection` |
| `Language`, `Scenario Type`, `Expected Keywords`, `Expected Classification`, `Expected Journey` | direct read |

**The `TestCase` dataclass:**
```python
@dataclass
class TestCase:
    test_id: str
    scenario_type: str        # "single-turn" or "multi-turn"
    language: str             # "en", "hi", "hing", etc.
    input_messages: list[str]  # ordered list of user messages
    expected_keywords: list[str]  # bot reply should contain at least one
    expected_classification: str  # optional scam type to check
    expected_journey: str        # optional flow name
    expected_emotion: str        # optional emotion to check
    notes: str
    source_sheet: str
```

---

### `test_boxx_scam_flows.py` — The Test Suite

**Purpose:** Where tests run, assertions happen, and results are reported.

**How it works:**

**Test Functions:**
1. `test_health_check` — relies on the session-level health check that already ran
2. `test_sample_quick` — quick one-shot test using the `/quick` endpoint
3. `test_boxx_scenarios` — the **main parametrized test**, one instance per loaded test case

**Per-test-execution flow:**

```
For one test case (test_id, language, messages, keywords, classification, journey):

  1. boxx_client.create_session(language)
     └── POST /api/test/session

  2. boxx_client.agree_to_disclaimer(session_id)
     └── POST .../message { button_id: "agree_disclaimer" }

  3. For each user_message in input_messages:
       boxx_client.send_message(session_id, message)
       ├── Assert reply is non-empty
       ├── Collect reply text and analysis
       └── Loop

  4. Assertions on final turn:
       ├── At least 1 expected_keyword in reply (ANY-match)
       ├── expected_classification in analysis field OR reply text
       ├── expected_journey in analysis.journey
       └── expected_emotion in analysis.emotion
```

**Smart Assertions:**

| Assertion | Strategy | Example | On failure |
|-----------|----------|---------|------------|
| Keywords | **ANY-match** — at least one keyword must appear in the reply | `["phishing", "scam"]` → bot says "Phishing Scam" ✓ | Prints full reply + input |
| Classification | Check `analysis.classification` first, fall back to reply text | Expected `phishing`, analysis is empty but reply says "Phishing Scam" ✓ | If both empty and single-turn test → **warning only** (bot may not have classified yet) |
| Journey | Exact match against `analysis.journey` | Expected `Flow2`, analysis says `Flow2` ✓ | Fail with analysis dump |

**Results CSV Output:**
Every test run generates a timestamped CSV file in `results/` with full per-test data:

```bash
results/boxx_results_20260728_091500.csv   # timestamped
results/boxx_results_latest.csv            # always the most recent run
```

Each CSV contains **all API response fields** for every test case:

| Column | Source | Example |
|--------|--------|---------|
| `test_id` | Test data | `TC_KYC_001` |
| `status` | PASS/FAIL/ERROR | `PASS` |
| `classification` | `analysis.classification` | `phishing` |
| `journey` | `analysis.journey` | `check_scam` |
| `emotion` | `analysis.emotion` | — |
| `loss_assessment` | `analysis.loss_assessment` | `no_loss` |
| `persona_archetype` | `analysis.persona_archetype` | `urban_mixed_general` |
| `persona_confidence` | `analysis.persona_confidence` | `0.2` |
| `response_style` | `analysis.response_style` | `default` |
| `keywords_matched` | Which expected keywords were found | `phishing \| scam` |
| `expected_not_found` | Keywords that were missing | `family` |
| `bot_reply` | Full response (500 chars) | *Give me a second...* |
| `full_analysis` | Complete analysis JSON | `{'classification': ''...}` |
| `error_message` | Error details if failed | `Classification mismatch...` |
| `input_messages` | All user turns joined | `\|` separated |

The CSV file includes a metadata header with run timestamp, source, duration, and pass/fail counts, plus a summary footer.

**Per-test logs:** Every turn is logged with latency, reply preview, and assertion results

**Session-finish summary:** A plain-text table printed at the end:
```
====================================================================================================
  BOXX TEST AUTOMATION — SUMMARY
====================================================================================================
  Test ID              Result   Lang   Latency    Classification       Scenario
  --------------------------------------------------------------------------------------------------
  TC_KYC_001           PASS     en     5432ms     phishing             KYC phishing - positive
  TC_OTP_001           PASS     en     3891ms     otp_fraud            OTP shared - positive case
  ...
  --------------------------------------------------------------------------------------------------
  TOTAL: 558  |  PASS: 558  |  FAIL: 0
====================================================================================================
```
- **HTML report:** With `--html=report.html --self-contained-html` for shareable reports
- **On failure:** The full bot reply, analysis object, and inputs are printed

---

### `conftest.py` — Pytest Configuration

**Purpose:** Fixtures, hooks, and test parametrization.

**Key components:**

| Component | What it does |
|-----------|-------------|
| `pytest_addoption` | Adds CLI flags: `--test-sheet`, `--base-url`, `--api-key`, `--results-dir` |
| `pytest_generate_tests` | Loads test cases at **collection time** and parametrizes `test_boxx_scenarios` |
| `boxx_client` fixture | Creates one `BOXXClient` per session, runs health check, fails fast if unreachable |
| `pytest_sessionfinish` | Writes timestamped results CSV to `results/` directory with all API response data per test |
| `test_loader.TestCase.__test__` | Prevents the dataclass from being collected as a test |

**Environment variables:**
| Variable | Default | Purpose |
|----------|---------|---------|
| `BOXX_BASE_URL` | `https://boxxv2.shunyalabs.ai` | API endpoint |
| `BOXX_API_KEY` | `boxx-qa-e1ae28770694f29b7ebc2cab3743438a` | API authentication |

---

### `pyproject.toml` — Pytest Configuration

```
[tool.pytest.ini_options]
testpaths = ["."]
log_cli = true                              # Show logs in terminal
log_cli_level = "INFO"                      # Default log level
addopts = "-v"                              # Verbose by default
markers = ["smoke", "sample"]               # Custom markers
```

HTML report is generated via CLI: `--html=report.html --self-contained-html`

---

## 5. How Test Execution Works

### Collection Phase (what happens before any test runs)

```
pytest starts
    │
    ├── pytest_generate_tests() in conftest.py
    │   ├── Check for --test-sheet flag
    │   ├── If found: load_comprehensive_test_cases(path)
    │   │   ├── .xlsx  → _load_from_xlsx() → iterate sheets → map columns → create TestCases
    │   │   └── .csv   → _load_from_csv()  → DictReader → create TestCases
    │   ├── If not found: load_sample_cases() → 8 built-in TestCases
    │   └── parametrize(test_boxx_scenarios, test_cases, ids=[test_id, ...])
    │
    └── boxx_client() fixture [session-scoped, runs once]
        ├── Create BOXXClient
        ├── Run health_check()
        └── FAIL FAST if API unreachable
```

### Execution Phase

```
For each parametrized test case:
    ├── boxx_client.create_session(language)
    ├── boxx_client.agree_to_disclaimer(session_id)
    ├── For each turn in input_messages:
    │   ├── boxx_client.send_message(session_id, message)
    │   ├── Assert reply non-empty
    │   └── Collect reply + analysis
    ├── Assert keywords (ANY-match)
    ├── Assert classification (if specified)
    ├── Assert journey (if specified)
    └── [Pass/Fail with details]

After all tests:
    └── pytest_sessionfinish() → print summary table
```

### Timing

- Each test takes **10–30 seconds** (API latency + LLM processing)
- 10 sample tests: ~2 minutes
- **558 CSV tests: ~1.5–3 hours (full run)
- 513 Excel tests: ~2–4 hours (full run)
- Use -k flag to run specific tests for faster iteration (e.g. -k "TC_KYC" for just phishing tests)
- Use `-k` flag to run specific tests for faster iteration

---

## 6. Test Case Coverage

### Built-in Sample (8 tests)
Runnable immediately without any sheet file — good for verifying the API is working.

### Comprehensive CSV (558 tests across 64 categories)

| # | Category | Tests | What's tested |
|---|----------|-------|---------------|
| 1 | KYC / Phishing | 9 | SBI/HDFC/ICICI brand phishing, Aadhaar KYC, ATM card, Netflix brand, Hindi/Hinglish variants, "is this genuine?" |
| 2 | OTP / Vishing | 8 | Bank call OTP, RBI impersonation, KYC OTP, CVV theft, TRAI impersonation, Hindi/Hinglish |
| 3 | UPI Fraud | 8 | Wrong transfer, GPay no delivery, UPI collect request, double debit, unauthorized, PhonePe |
| 4 | QR Code Scam | 6 | Pull payment, cashback, marketplace, merchant, Hindi variant |
| 5 | Remote Access | 7 | AnyDesk, TeamViewer, QuickSupport, APK sideload, preventive path, credit limit scam |
| 6 | Digital Arrest | 7 | Police video call, CBI, cyber crime summons, money under threat, "is it genuine?" |
| 7 | Job Fraud | 8 | WFH registration fee, data entry, Telegram tasks, WhatsApp interview, brand impersonation |
| 8 | Investment Scam | 6 | Stock trading Telegram, daily returns app, crypto locked, forex, money doubling |
| 9 | Marketplace Fraud | 7 | OLX fake payment, Facebook no delivery, Instagram store, fake customer care, COD switch |
| 10 | Loan App Scam | 6 | Threats, data theft, predatory interest, Hindi, genuine loan query |
| 11 | Sextortion | 5 | Social media, video call recording, camera hack, Hindi, dating app |
| 12 | Card Fraud | 5 | International transaction, ATM skimming, cloning, multi-turn, POS machine risk |
| 13 | SIM Swap | 4 | SIM stopped, change request, account accessed, unauthorized porting |
| 14 | Identity Theft | 6 | Aadhaar on Telegram, PAN misuse, lost Aadhaar, fraudulent loan, Hindi, safety |
| 15 | Lottery / Prize | 5 | 25 lakh win, iPhone prize, GPay lucky draw, Hindi, visa lottery |
| 16 | Fake Ads | 5 | Facebook 90% off, Instagram ad, Flipkart WhatsApp, free iPhone shipping |
| 17 | Public WiFi | 4 | Airport banking, hotel WiFi, data interception, VPN safety |
| 18 | General Cyber | 6 | WhatsApp hacked, email spam, malware, social media takeover, phone cloning |
| 19 | Negative Cases | 18 | Genuine bank SMS, Amazon/Flipkart, insurance, bill, password tips, 2FA, Aadhaar safety |
| 20 | Out of Scope | 18 | Weather, jokes, capital city, math, pizza, biryani, cricket, poems, philosophy |
| 21 | Edge Cases | 26 | Empty, emoji-only, single char, gibberish, long, incomplete, unethical, urgent, numbers, special chars, duplicate, dots, ? marks, "No", "Yes" |
| 22 | Emotional / Distressed | 5 | Suicidal, life savings lost, scared, shame, family impact |
| 23 | Multi-turn Flows | 16 | Phishing click→recovery, SIM swap→account, job→progressive payments, OLX→QR scam, crypto platform shut, AI voice clone, loan app→blackmail |
| 24 | Fraudster Queries | 4 | "How to scam", "phishing template", "fake UPI screenshot", "clone ATM card" |
| 25 | Mixed Scams | 5 | Job+identity, UPI+job, ambiguous, hacked+sextortion, multiple paid |
| 26 | Button Interactions | 6 | No interaction (Flow3), Yes (Flow1), No debit (Flow4), Yes debit (Flow2), Not sure |
| 27 | Tech Support | 4 | Microsoft virus, scareware popup, antivirus renewal, Dell warranty |
| 28 | Rental Scams | 3 | Magicbricks, Facebook deposit, Housing.com overpayment |
| 29 | Charity Scams | 3 | Cancer donation, earthquake relief, orphanage QR |
| 30 | Escalation | 4 | Human agent, supervisor, language switch |

**Expanded Sections (31–64):**

| # | Category | Tests | What's tested |
|---|----------|-------|---------------|
| 31 | Hinglish / Romanized Hindi | 30 | Pure Hinglish: "Maine OTP bata diya", "Mera WhatsApp hack ho gaya", "GPay se paise gaye" |
| 32 | Panicked Typing | 15 | ALL CAPS, repeating: "HELP HELP HELP", "BHAI BHAI BHAI", "Kya karun kya karun" |
| 33 | Indian English | 15 | "Kindly do the needful", "Myself Ramesh", "Do one thing", "I am having one issue" |
| 34 | Deepfake / AI Voice | 10 | AI voice clone, deepfake video, WhatsApp voice note cloning |
| 35 | Courier / Parcel | 10 | FedEx NCB drugs, DHL customs, India Post, Blue Dart, Amazon delivery |
| 36 | FASTag / Toll | 10 | NHAI scams, FASTag KYC link, double debit, fake NPCI payment link |
| 37 | Government Scheme | 15 | PM Kisan, Ayushman Bharat, MGNREGA, EPFO, Income Tax refund, GST |
| 38 | Utility Bill | 10 | Electricity 50% off, gas cylinder booking, water bill, LPG subsidy, broadband |
| 39 | Telecom / SIM | 10 | Jio/Airtel free recharge, SIM upgrade KYC, TRAI calls, 5G upgrade |
| 40 | Matrimony / Dating | 10 | Shaadi.com, Jeevansathi, Tinder, NRI marriage, Instagram love scam |
| 41 | Real Estate | 10 | Housing.com, Nobroker, property registry fraud, builder scam, overpayment |
| 42 | Education / Exam | 10 | NEET rank scam, solved papers, PhD donation, abroad consultancy, certificate fee |
| 43 | Medical / Health | 10 | Fake hospital emergency, kidney donor, vaccine survey, insurance claim |
| 44 | Crypto / Bitcoin | 10 | Cloud mining, NFT, USDT P2P frozen, Web3 gaming, arbitrage bot |
| 45 | WhatsApp Group | 10 | "Invest 2000 get 25000", stock tips, task scams, admin threats, fake channel |
| 46 | Social Media | 10 | YouTube Bitcoin ads, Instagram reels, Telegram trading, Snapchat blackmail |
| 47 | Typing Mistakes | 10 | Real fat-finger: "otb", "mre mobail", "soi ne pocli ce call kee" |
| 48 | Third-Party Reports | 12 | "My father", "my mother", "meri mummy", "my uncle", "my boss", "my sister" |
| 49 | Angry / Frustrated | 10 | "You people are useless", "this bot is a scam too", "nobody helps" |
| 50 | Very Short Inputs | 15 | "Scam", "Hacked", "Money gone", "OTP shared", "Blackmail", "Help needed" |
| 51 | Numbers / IDs | 10 | UTR numbers, transaction IDs, account numbers, IFSC, card last 4 digits |
| 52 | Story Narratives | 10 | Timeline: "First they called then I clicked then money gone..." |
| 53 | Elderly / Vulnerable | 10 | "Beta mere account se paise nikal gaye", "I'm 70 years old", "passbook taken" |
| 54 | Scam Text Copy-Paste | 10 | "They sent: Dear Customer your SBI bank account will be suspended..." |
| 55 | Regional Mix | 10 | Tamil, Telugu, Marathi, Bengali, Gujarati words mixed in English |
| 56 | Location-specific | 10 | Mumbai, Bangalore, Delhi, Pune, Chennai, Hyderabad, Kolkata, Lucknow |
| 57 | Urgency Variants | 10 | "They're on the phone NOW!", "I'm at the ATM", "10 minutes to transfer" |
| 58 | Looping User | 10 | "Hello", "Are you there", "Please reply", "Why no answer" |
| 59 | Special Scenarios | 10 | Domain renewal, Instagram hacked, ransom note, fake advocate, visa fraud |
| 60 | More Negative | 10 | Password tips, 2FA, genuine UPI transfer, save card on Amazon, Paytm safety |
| 61 | Forwarded Messages | 10 | WhatsApp chain forwards: "Jio free 5G", "LIC bonus", "WhatsApp gold", "PM Modi scheme" |
| 62 | More Multi-turn | 8 | Complex 5-turn flows: fake Amazon care, Telegram job, crypto scam, AI voice clone |
| 63 | More Edge Cases | 15 | Emoji-only, question marks, dots, "No", "Yes", "Maybe", "Ok", "Thanks" |
| 64 | More Out of Scope | 12 | Capital of France, biryani recipe, cricket, poem, homework, time |

### Existing Excel (513 test cases across 17 sheets)
- `Boxx_Sheet_Test_Cases` — 97 cases
- `AUTH_GATE` — 9 cases (auth flows)
- `FLOW1` — 18 cases (intake/triage)
- `FLOW2` — 18 cases (recovery)
- `FLOW3_No_Action` — 8 cases (no action taken)
- `FLOW4-5_Preventive & SIMSwap` — 11 cases
- `Hindi & Hinglish` — 35 cases
- `AI Behaviour` — 32 cases
- `Backend_Conversation_Validation` — 5 cases
- `UC02-3_Phishing & Investment sc` — 11 cases
- `Remote_Access & KYC` — 14 cases
- `Digital Arrest & Loan Apps` — 10 cases
- `Job fraud, Marketplace & Sexort` — 15 cases
- `QR code & Addhar` — 9 cases
- `Cards & Fake Loan` — 19 cases
- `Wifi & Lottery prize` — 20 cases
- `Fake Adds & General Cyber` — 15 cases
- `Automation_Test_Suite` — 264 cases (derived from the comprehensive CSV)

---

## 7. Commands Cheat Sheet

### Quick Start (sample tests, no sheet needed)

```bash
# Install dependencies
pip install -r requirements.txt

# Run all 10 sample tests
pytest -v

# Run with HTML report
pytest --html=report.html --self-contained-html -v

# Run only smoke tests
pytest -v -m smoke
```

### Running With Test Sheets

```bash
# Comprehensive CSV (558 tests, 64 categories)
pytest -v --test-sheet=comprehensive_test_cases.csv

# Existing Excel workbook (513 tests, 17 sheets)
pytest -v --test-sheet="Docs/Boxx Master Testcases.xlsx"

# With HTML report from CSV
pytest --html=report.html --self-contained-html -v --test-sheet=comprehensive_test_cases.csv
```

### Running Specific Tests

```bash
# Single test by exact test ID
pytest -v -k "TC_KYC_001"
pytest -v -k "SAMPLE_005"

# Multiple test IDs
pytest -v -k "TC_KYC_001 or TC_OTP_001 or TC_UPI_001"

# All tests in a category (using test_id prefix)
pytest -v -k "TC_MT_"

# All tests of a specific type
pytest -v -k "scenario"  # searches parametrized names

# Exclude tests
pytest -v -k "not TC_OOS_"
```

### Results CSV Output

Every test run automatically saves detailed results:

```bash
# Results are saved after every run — no extra flags needed
pytest -v

# Check the latest results
less results/boxx_results_latest.csv

# List all historical result files
ls -la results/boxx_results_*.csv

# Custom results directory
pytest -v --results-dir=/path/to/my/results
```

### Configuration Options

```bash
# Custom API URL/key
pytest -v --base-url="https://your-api.com" --api-key="your-key"

# Custom results directory
pytest -v --results-dir=./my-results/

# Environment variables (preferred for CI)
export BOXX_BASE_URL="https://boxxv2.shunyalabs.ai"
export BOXX_API_KEY="boxx-qa-e1ae28770694f29b7ebc2cab3743438a"
pytest -v

# Quiet mode (only show failures and summary)
pytest -v --tb=short -o "log_cli_level=WARNING"

# Show local variables on failure
pytest -v --tb=long --showlocals
```

### Performance

```bash
# Run a single test to verify the API is responding
pytest -v -k "SAMPLE_001"

# Run a quick subset to test multiple categories
pytest -v -k "TC_KYC_001 or TC_OTP_001 or TC_UPI_001 or TC_MKT_001 or TC_JOB_001"

# Full comprehensive run (can take 1.5-3 hours)
time pytest -v --test-sheet=comprehensive_test_cases.csv --tb=line

# Quick run of a single category
time pytest -v --test-sheet=comprehensive_test_cases.csv --tb=line -k "TC_KYC_"
```

---

## 8. What We Expect From the Bot

### For Scam Reports (Positive Cases)

| Input Type | Expected Bot Behavior | Example Response Contains |
|------------|----------------------|---------------------------|
| Phishing/KYC SMS | Classify as phishing, ask if money debited | "Phishing Scam", "fake link", "urgent" |
| OTP shared | Identify OTP fraud, start recovery | "OTP", "fraud", "bank", "block" |
| UPI fraud/money sent | Empathy + ask payment method + recovery | "UPI", "recovery", "1930", "disable" |
| QR code scan debit | Identify QR pull scam, start recovery | "QR", "scam", "disable UPI" |
| Remote access app installed | Classify remote access scam | "remote", "access", "AnyDesk" |
| Digital arrest / police call | Reassure + identify digital arrest scam | "scam", "police", "arrest", "don't pay" |
| Job fraud | Classify recruitment scam | "job", "registration", "scam" |
| Investment scam | Identify investment fraud | "investment", "scam", "guarantee" |
| Marketplace fraud | Classify marketplace fraud | "marketplace", "payment", "scam" |
| Loan app harassment | Classify loan app scam | "loan", "scam", "threat" |
| Sextortion / blackmail | Classify + guide to report | "blackmail", "help", "report" |
| Card fraud | Classify card skimming/cloning | "card", "fraud", "block" |
| SIM swap | Identify SIM swap | "SIM", "swap", "fraud" |
| Identity (Aadhaar) misuse | Identify identity theft | "Aadhaar", "identity", "misuse" |

### For Negative / Non-Scam Inputs

| Input Type | Expected Bot Behavior |
|------------|----------------------|
| Genuine bank SMS | No false positive — not flagged as scam |
| Amazon/Flipkart shipping updates | Treated as non-scam or redirected to cyber topics |
| Insurance/bill reminders | Treat as non-scam |
| Educational queries about safety | Provide safety advice |
| General security questions | Provide helpful guidance |

### For Out-of-Scope / Non-Cyber Queries

| Input Type | Expected Bot Behavior |
|------------|----------------------|
| Weather, jokes, math, geography | Redirect to cyber topics: "I can only help with cyber fraud" |
| Food/movie recommendations | Same redirect |

### For Edge Cases

| Input Type | Expected Bot Behavior |
|------------|----------------------|
| Empty message | Return error or prompt for input |
| Emoji-only | Handle gracefully, still respond |
| Very long message | Process without crashing |
| Unethical request (how to scam) | Refuse to assist |
| Urgent (fraud in progress) | Prioritize with immediate action steps |

### For Language

| Language | Expected Bot Behavior |
|----------|----------------------|
| English (en) | Respond in English |
| Hindi (hi) | Respond in Hindi |
| Hinglish (hing) | Respond in Hinglish or Hindi |
| Mixed languages | Maintain language context within session |

---

## 9. Interpreting Failures

### Common Failure Patterns

**1. Missing expected keywords**
```
TC_KYC_001 FAILED
  No expected keyword found in bot reply.
  Expected (any of): ['happening', 'family', 'you']
  Bot reply:  Give me a second, I'm checking this properly for you.
```
→ The bot gave a different response this time. Keywords need updating. The bot's responses vary (that's normal for an AI model). Either:
- Add more keywords to cover the variation
- Change keywords to match the new response pattern
- The bot may have changed behavior after an update

**2. Classification mismatch**
```
TC_CARD_001 FAILED
  Classification 'card_fraud' not found in analysis or reply.
```
→ The bot didn't classify this as card fraud. Either:
- The input didn't trigger card-specific classification
- The bot routed differently (e.g., intake question first)
- Remove `expected_classification` for this test (set it to empty)

**3. Journey mismatch**
```
TC_OOS_001 FAILED
  Journey mismatch.
  Expected (contains): out of scope - general query
  Got: (empty)
```
→ The `expected_journey` field has notes text instead of a valid journey name. Fix the test data.

**4. Timeout**
```
TC_SAMPLE_004 FAILED
  Request timed out after 45s
```
→ The API took too long to respond. The bot's LLM pipeline can be slow for certain languages or complex inputs. Check:
- Is the API under load?
- Is the specific language model slow?
- Retry the test — it may be a transient issue

**5. API Error**
```
TC_RA_001 FAILED
  API returned 404 for POST /api/test/session/abc/message
```
→ The session ID was invalid or expired. Check for session reuse (each test must create its own session).

### How to Diagnose a Failure

Every failure prints:
- **Test ID** — which test case failed
- **Expected** — what you wanted to find (keywords, classification, journey)
- **Bot reply** — the full bot response
- **Bot (lower)** — lowercased version for case-insensitive checking
- **Full analysis** — the complete analysis object from the API
- **Inputs** — what the user sent

This is enough info to either fix the test data or identify a bot issue.

---

## 10. Adding New Test Cases

### Method 1: Add to the Comprehensive CSV

Add a new row to `comprehensive_test_cases.csv`:

```csv
TC_MY_001,en,single-turn,I received a fake message from my bank about a reward point expiry,phishing|scam|reward,phishing,,Reward point phishing scam
```

| Column | Required | Description |
|--------|----------|-------------|
| `test_id` | ✅ | Unique ID for identification |
| `language` | ✅ | `en`, `hi`, `hing`, etc. |
| `scenario_type` | ✅ | `single-turn` or `multi-turn` |
| `input_message` | ✅ | The user's input. Use `|` for multi-turn |
| `expected_keywords` | ✅ | Pipe-separated keywords (bot must match at least one) |
| `expected_classification` | Conditionally | Scam type to check (omit if bot asks intake questions first) |
| `expected_journey` | Optional | Flow name to check (Flow1, Flow2, etc.) |
| `notes` | Optional | Description of what this tests |

### Method 2: Add to the Excel Workbook

Add a new sheet with any column layout — the loader auto-detects columns by name. Known-mapped column names:

| Your column name | Must contain |
|-----------------|-------------|
| User Input / Steps / User Query | The user message text |
| Expected Result / Expected Behaviour | Expected bot behavior description |
| TC ID / Test Case / Test ID | Unique identifier |
| Scenario | Test description |

**Multi-turn:** Separate messages with `|` in the cell.

### Method 3: Build a Separate CSV

Create a new CSV file with any of these column names and pass it with `--test-sheet`:

```
test_id,language,scenario_type,input_message,expected_keywords,expected_classification,expected_journey,notes
```

---

## 11. CI/CD Integration

### GitHub Actions Example

```yaml
name: BOXX Test Suite
on: [push, pull_request, schedule]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests (comprehensive CSV)
        run: |
          pytest -v --html=report.html --self-contained-html \
            --test-sheet=comprehensive_test_cases.csv
      
      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: boxx-test-report
          path: report.html
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | Some tests failed |
| 2 | Test execution interrupted (timeout, etc.) |
| 3+ | Internal error |

### Test Categorization for Pipelines

```bash
# Smoke test (quick check - 30 seconds)
pytest -v -m smoke

# Quick sanity (sample tests - 2 minutes)
pytest -v

# Full regression (comprehensive CSV - 1.5-3 hours)
pytest -v --test-sheet=comprehensive_test_cases.csv

# Full regression (all Excel - 2-4 hours)
pytest -v --test-sheet="Docs/Boxx Master Testcases.xlsx"
```

---

## 12. Test Case Inventory

### Built-in Samples (8 tests)
```
SAMPLE_001 — KYC phishing SMS
SAMPLE_002 — Bank OTP call
SAMPLE_003 — Phishing link clicked, no debit
SAMPLE_004 — Hindi: paisa cut gaya
SAMPLE_005 — Facebook Marketplace no delivery
SAMPLE_006 — Hindi: police video call threat
SAMPLE_007 — "Is this genuine?" query about ICICI
SAMPLE_008 — Out of scope: weather query
```

### Comprehensive CSV (558 tests)
Full inventory at `comprehensive_test_cases.csv`. Test IDs follow the pattern:

**Original 30 categories:**
```
TC_KYC_001..009  — Phishing / KYC scans
TC_OTP_001..008  — OTP / vishing
TC_UPI_001..008  — UPI fraud
TC_QR_001..006   — QR code scams
TC_RA_001..007   — Remote access
TC_DA_001..007   — Digital arrest
TC_JOB_001..008  — Job fraud
TC_INV_001..006  — Investment scams
TC_MKT_001..007  — Marketplace fraud
TC_LOAN_001..006 — Loan app scams
TC_SEX_001..005  — Sextortion
TC_CARD_001..005 — Card fraud
TC_SIM_001..004  — SIM swap
TC_IDT_001..006  — Identity theft
TC_LOT_001..005  — Lottery / prize
TC_AD_001..005   — Fake ads
TC_WIFI_001..004 — Public WiFi risk
TC_CYB_001..006  — General cyber
TC_NEG_001..008  — Negative / genuine cases
TC_OOS_001..006  — Out of scope
TC_EDGE_001..011 — Edge / corner cases
TC_EMO_001..005  — Emotional / distressed
TC_MT_001..008   — Multi-turn flows
TC_FS_001..004   — Fraudster queries
TC_MIX_001..005  — Mixed scam types
TC_BTN_001..006  — Button interactions
TC_TEC_001..004  — Tech support scams
TC_RENT_001..003 — Rental scams
TC_CHAR_001..003 — Charity scams
TC_ESC_001..004  — Escalation requests
```

**Expanded categories (31–64):**
```
TC_HING_702..731     — Romanized Hindi / Hinglish
TC_PANIC_732..746    — Panicked / ALL CAPS typing
TC_INDENG_747..761   — Indian English
TC_AI_762..771       — Deepfake / AI voice scams
TC_COURIER_772..781  — Courier / parcel scams
TC_FASTAG_782..791   — FASTag / toll scams
TC_GOVT_792..806     — Government scheme scams
TC_BILL_807..816     — Utility bill scams
TC_TELECOM_817..826  — Telecom / SIM scams
TC_MATRIMONY_827..836 — Matrimony / dating scams
TC_PROPERTY_837..846  — Real estate scams
TC_EDU_847..856      — Education / exam scams
TC_HEALTH_857..866   — Medical / health scams
TC_CRYPTO_867..876   — Crypto / Bitcoin scams
TC_WA_SCAM_877..886  — WhatsApp group scams
TC_SOCIAL_887..896   — Social media scams
TC_TYPO_897..906     — Typing mistakes
TC_3PARTY_907..918   — Third-party reporting
TC_ANGRY_919..928    — Angry / frustrated users
TC_SHORT_929..943    — Very short / telegraphic
TC_NUM_944..953      — Numbers / transaction IDs
TC_STORY_954..963    — Story / timeline narratives
TC_ELDERLY_964..973  — Elderly / vulnerable users
TC_COPY_974..983     — Scam text copy-paste
TC_REGIONAL_984..993 — Regional language mix
TC_LOCATION_994..1003 — Location-specific scams
TC_URGENT_1004..1013 — Time-sensitive / urgency
TC_LOOP_1014..1023   — Repetitive / looping user
TC_SPECIAL_1024..1033 — Special scenarios
TC_NEG2_1034..1043   — More negative cases
TC_FWD_1044..1053    — Forwarded chain messages
TC_OOS2_1054..1065   — More out of scope
TC_EDGE2_1066..1080  — More edge cases (emoji, dots, single words)
TC_MTFLOW_1081..1088 — More multi-turn complex flows
```

### Excel Workbook (513 tests)
Covers all 17 existing sheets in `Docs/Boxx Master Testcases.xlsx`, providing historical continuity with previously written test cases.

---

## Quick Reference Card

```
┌───────────────────────────────────────────────────────────────────┐
│                    BOXX TESTING IN 30 SECONDS                     │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Install:   pip install -r requirements.txt                    │
│  2. Run:       pytest -v                                         │
│  3. HTML:      pytest --html=report.html --self-contained-html    │
│  4. Full:      pytest -v --test-sheet=comprehensive_test_cases.csv│
│  5. Results:   less results/boxx_results_latest.csv               │
│                                                                   │
│  Test data sources (auto-detected):                               │
│    • Built-in: 8 sample cases (default, no file needed)           │
│    • CSV:      558 cases, 64 categories (--test-sheet=compre...)  │
│    • Excel:    513 cases, 18 sheets (--test-sheet=Docs/...)       │
│                                                                   │
│  Key behavior:                                                    │
│    • Each test gets a FRESH session                               │
│    • Disclaimer is auto-accepted                                  │
│    • Keywords use ANY-match (not ALL-match)                       │
│    • Classification checks both analysis field AND reply text     │
│    • Full bot reply + analysis saved to results CSV               │
│    • Plain-text summary table + detailed CSV at end               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

*Document version 1.0 — Last updated: 2026-07-28*
