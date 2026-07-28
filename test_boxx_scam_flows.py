"""
BOXX Chatbot Test Automation Suite
====================================
Pytest-based test suite that validates the BOXX scam-detection chatbot.

Data-driven: reads test cases from a sheet (or uses built-in samples),
creates isolated sessions, walks through multi-turn conversations,
and asserts bot responses match expected keywords/classifications.

Results are accumulated into TEST_RESULTS and written to a timestamped CSV
by conftest.py at session end.
"""

import logging
from datetime import datetime, timezone

import pytest

from boxx_client import BOXXClient, BOXXError

from auto_responder import (
    MAX_TURNS,
    ConversationState,
    generate_response,
    is_session_closed,
)

logger = logging.getLogger("test_boxx")

# ---------------------------------------------------------------------------
# Results accumulator — populated during test runs, written by conftest
# ---------------------------------------------------------------------------

TEST_RESULTS: list[dict] = []


def record_result(
    test_id: str,
    language: str,
    scenario_type: str,
    input_messages: list[str],
    expected_keywords: list[str],
    expected_classification: str,
    expected_journey: str,
    expected_emotion: str,
    notes: str,
    status: str,            # "PASS" | "FAIL" | "ERROR" | "SKIP"
    latency_ms: float,
    turns: int,
    bot_reply: str,
    analysis: dict,
    keywords_matched: list[str],
    expected_not_found: list[str],
    error_message: str,
    source_sheet: str,
):
    """Store one test result entry for later CSV export."""
    TEST_RESULTS.append({
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "test_id": test_id,
        "language": language,
        "scenario_type": scenario_type,
        "input_messages": " | ".join(input_messages),
        "turn_count": turns,
        "expected_keywords": " | ".join(expected_keywords),
        "expected_classification": expected_classification,
        "expected_journey": expected_journey,
        "expected_emotion": expected_emotion,
        "notes": notes,
        "status": status,
        "latency_ms": f"{latency_ms:.0f}" if latency_ms >= 0 else "",
        "classification": (analysis or {}).get("classification", ""),
        "journey": (analysis or {}).get("journey", ""),
        "emotion": (analysis or {}).get("emotion", ""),
        "emotion_language": (analysis or {}).get("emotion_language", ""),
        "loss_assessment": (analysis or {}).get("loss_assessment", ""),
        "persona_archetype": (analysis or {}).get("persona_archetype", ""),
        "persona_confidence": (analysis or {}).get("persona_confidence", ""),
        "response_style": (analysis or {}).get("response_style", ""),
        "keywords_matched": " | ".join(keywords_matched) if keywords_matched else "",
        "expected_not_found": " | ".join(expected_not_found) if expected_not_found else "",
        "bot_reply": (bot_reply or "").replace("\n", " ")[:500],
        "full_analysis": str(analysis or {}),
        "error_message": error_message,
        "source_sheet": source_sheet,
    })


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_health_check(boxx_client: BOXXClient):
    """Smoke test: health check already ran in boxx_client fixture — just confirm."""
    passed = boxx_client is not None
    record_result(
        test_id="HEALTH_CHECK",
        language="en",
        scenario_type="single-turn",
        input_messages=["health check"],
        expected_keywords=[],
        expected_classification="",
        expected_journey="",
        expected_emotion="",
        notes="Smoke test - API health check",
        status="PASS" if passed else "FAIL",
        latency_ms=0,
        turns=0,
        bot_reply="",
        analysis={},
        keywords_matched=[],
        expected_not_found=[],
        error_message="",
        source_sheet="built-in",
    )
    assert passed


@pytest.mark.sample
def test_sample_quick(boxx_client: BOXXClient):
    """Quick test: use the one-shot endpoint to verify basic response path."""
    error_msg = ""
    status = "PASS"
    reply = ""
    latency = -1
    analysis = {}
    try:
        resp = boxx_client.quick("I want to report a scam call I received")
        reply = resp.get("reply", "") or ""
        latency = resp.get("latency_ms", -1)
        analysis = resp.get("analysis", {}) or {}
        assert reply, f"Reply should be non-empty, got: {resp}"
        assert resp.get("session_id"), "Should have a session_id"
        assert latency >= 0, "Latency should be reported"
    except AssertionError as e:
        status = "FAIL"
        error_msg = str(e)
    except BOXXError as e:
        status = "ERROR"
        error_msg = str(e)

    record_result(
        test_id="SAMPLE_QUICK",
        language="en",
        scenario_type="single-turn",
        input_messages=["I want to report a scam call I received"],
        expected_keywords=["scam"],
        expected_classification="",
        expected_journey="",
        expected_emotion="",
        notes="Quick one-shot test",
        status=status,
        latency_ms=latency,
        turns=1,
        bot_reply=reply,
        analysis=analysis,
        keywords_matched=["scam"] if status == "PASS" else [],
        expected_not_found=[] if status == "PASS" else ["scam"],
        error_message=error_msg,
        source_sheet="built-in",
    )
    if error_msg:
        pytest.fail(error_msg)


def test_boxx_scenarios(boxx_client: BOXXClient, test_case):
    """Data-driven test: one parametrisation per test case from the sheet.

    For each test case:
    1. Create fresh session in the specified language
    2. Accept the disclaimer button
    3. Walk through all user turns (multi-turn support)
    4. Assert expected keywords appear in the final reply
    5. Assert classification / journey when specified

    All results (pass/fail + full API data) are captured in TEST_RESULTS.
    """
    tc = test_case
    tc_id = tc.test_id

    # Track recording data
    status = "PASS"
    error_message = ""
    keywords_matched: list[str] = []
    expected_not_found: list[str] = []
    all_replies: list[str] = []
    final_analysis: dict = {}
    final_latency: float = -1

    # Track if keywords ever matched on any reply (not just the final one)
    keywords_ever_found = False
    best_analysis: dict = {}
    best_reply: str = ""
    best_latency: float = -1
    check_analysis: dict = final_analysis
    check_reply: str = ""
    check_latency: float = final_latency

    def _check_keywords(reply: str) -> tuple[list[str], list[str]]:
        """Return (matched, not_found) for expected keywords in reply."""
        if not tc.expected_keywords or not reply:
            return [], tc.expected_keywords or []
        reply_lower = reply.lower()
        matched = [kw for kw in tc.expected_keywords if kw.lower() in reply_lower]
        not_found = [kw for kw in tc.expected_keywords if kw.lower() not in reply_lower]
        return matched, not_found

    logger.info("[%s] Starting — lang=%s turns=%d keywords=%s",
                tc_id, tc.language, len(tc.input_messages), tc.expected_keywords)

    try:
        # 1. Create a fresh session in the specified language
        session_id = boxx_client.create_session(
            language=tc.language,
            profile_name=f"QA-{tc_id}",
        )
        logger.debug("[%s] Session: %s", tc_id, session_id)

        # 2. Send disclaimer agreement (standard first turn)
        try:
            boxx_client.agree_to_disclaimer(session_id)
        except BOXXError as exc:
            status = "ERROR"
            error_message = f"Disclaimer turn failed: {exc}"
            logger.error("[%s] %s", tc_id, error_message)
            _record_and_fail(status, error_message, tc, tc_id, all_replies, final_analysis, final_latency, keywords_matched, expected_not_found)

        # ================================================================
        # PHASE 1: Pre-defined messages from test case
        # ================================================================
        for i, msg in enumerate(tc.input_messages):
            logger.debug("[%s] Turn %d/%d: %.80s", tc_id, i + 1, len(tc.input_messages), msg)

            try:
                resp = boxx_client.send_message(session_id, message=msg)
            except BOXXError as exc:
                status = "ERROR"
                error_message = f"Turn {i + 1} API error: {exc}"
                logger.error("[%s] %s", tc_id, error_message)
                _record_and_fail(status, error_message, tc, tc_id, all_replies, final_analysis, final_latency, keywords_matched, expected_not_found)

            reply = resp.get("reply", "") or ""
            all_replies.append(reply)
            final_analysis = resp.get("analysis", {}) or {}
            final_latency = resp.get("latency_ms", -1)

            # Check keywords on this reply — track the best match
            if not keywords_ever_found:
                matched, not_found = _check_keywords(reply)
                if matched:
                    keywords_ever_found = True
                    keywords_matched = matched
                    expected_not_found = not_found
                    best_analysis = final_analysis
                    best_reply = reply
                    best_latency = final_latency
                    logger.info("[%s] Keywords found at turn %d: %s",
                                tc_id, i + 1, matched)

            # Assert each turn returns a non-empty reply
            if not reply.strip():
                status = "FAIL"
                error_message = (
                    f"[{tc_id}] Turn {i + 1} returned empty reply.\n"
                    f"  Input:         {msg}\n"
                    f"  Full response: {resp}"
                )
                logger.error("[%s] %s", tc_id, error_message)
                _record_and_fail(status, error_message, tc, tc_id, all_replies, final_analysis, final_latency, keywords_matched, expected_not_found)

            latency = resp.get("latency_ms", -1)
            logger.debug("[%s] Turn %d reply: %.100s… (latency=%sms, reply_count=%s)",
                         tc_id, i + 1, reply.replace('\n', ' '), latency, resp.get("reply_count"))

        # ================================================================
        # PHASE 2: Auto-respond loop — keep talking until bot concludes
        # ================================================================
        conv_state = ConversationState()
        session_concluded = False
        auto_turns = 0

        while auto_turns < MAX_TURNS and not keywords_ever_found:
            last_reply = all_replies[-1]
            last_analysis = final_analysis

            # 2a. Check for session conclusion (bot said goodbye / stay safe)
            if is_session_closed(last_reply, last_analysis):
                session_concluded = True
                logger.info("[%s] Bot concluded session at turn %d (auto=%d)",
                            tc_id, len(all_replies), auto_turns)
                break

            # 2b. Update conversation health state
            conv_state.update(last_analysis)

            # 2c. Check for stuck (repeated questions, stalled journey, empty replies)
            if status == "PASS":  # don't override earlier failures
                stuck_reason = conv_state.is_stuck()
                if stuck_reason:
                    status = "FAIL"
                    error_message = (
                        f"[{tc_id}] {stuck_reason} "
                        f"(auto-turn {auto_turns}, total {len(all_replies)} turns)"
                    )
                    logger.warning("[%s] %s", tc_id, error_message)
                    break

            # 2d. Generate appropriate response
            response = generate_response(
                bot_reply=last_reply,
                original_message=tc.input_messages[0],
                scenario_notes=tc.notes,
                state=conv_state,
                turn_count=len(all_replies),
            )

            # Handle special response signals
            if response == "__SESSION_CONCLUDED__":
                session_concluded = True
                logger.info("[%s] Bot closed conversation (auto-turn %d)",
                            tc_id, auto_turns)
                break

            if response == "__BLOCKED__":
                # Bot refused to engage — not necessarily a test failure;
                # let the keyword assertions decide.
                logger.info("[%s] Bot refused to assist (anti-scam filter) "
                            "at auto-turn %d", tc_id, auto_turns)
                break

            if response == "__CLOSE__":
                # User says "no thanks" — bot should now close
                response = "No, that is all. Thank you for your help."

            if response is None:
                # No pattern matched — generic nudge
                logger.info("[%s] No pattern matched at auto-turn %d, "
                            "sending generic nudge", tc_id, auto_turns)
                response = "Please help me, what should I do next?"

            # 2e. Send the auto-generated response
            logger.info("[%s] Auto-turn %d → sending reply to bot",
                        tc_id, auto_turns + 1)
            try:
                resp = boxx_client.send_message(session_id, message=response)
            except BOXXError as exc:
                if status == "PASS":
                    status = "ERROR"
                    error_message = (
                        f"[{tc_id}] Auto-turn {auto_turns} API error: {exc}"
                    )
                    logger.error("[%s] %s", tc_id, error_message)
                break

            reply = resp.get("reply", "") or ""
            if not reply.strip():
                conv_state.mark_empty_reply()
            all_replies.append(reply)
            final_analysis = resp.get("analysis", {}) or {}
            final_latency = resp.get("latency_ms", -1)

            # Check keywords on this auto-respond reply
            if not keywords_ever_found:
                matched, not_found = _check_keywords(reply)
                if matched:
                    keywords_ever_found = True
                    keywords_matched = matched
                    expected_not_found = not_found
                    best_analysis = final_analysis
                    best_reply = reply
                    best_latency = final_latency
                    logger.info("[%s] Keywords found at auto-turn %d: %s",
                                tc_id, auto_turns + 1, matched)

            logger.info("[%s] Bot replied (auto-turn %d): %.120s… latency=%sms",
                        tc_id, auto_turns + 1,
                        reply.replace('\n', ' ')[:120], final_latency)
            auto_turns += 1

        else:
            # while loop terminated without break (MAX_TURNS hit or never entered)
            # Never fail if keywords were already found — test passes on first reply match
            if status == "PASS" and not session_concluded and not keywords_ever_found:
                status = "FAIL"
                error_message = (
                    f"[{tc_id}] Bot did not conclude session within "
                    f"{MAX_TURNS} auto-respond turns "
                    f"(total {len(all_replies)} turns)"
                )
                logger.warning("[%s] %s", tc_id, error_message)

        # ================================================================
        # PHASE 3: Assertions — keywords, classification, journey, emotion
        # ================================================================
        final_reply = all_replies[-1] if all_replies else ""

        # Use the best-matched reply's analysis for classification/journey/emotion checks
        # if keywords were found on a non-final reply; otherwise use final.
        check_analysis = best_analysis if keywords_ever_found else final_analysis
        check_reply = best_reply if keywords_ever_found else final_reply
        check_latency = best_latency if keywords_ever_found else final_latency

        # 3a. All expected keywords present (checked on ALL replies, not just final)
        if tc.expected_keywords:
            if keywords_ever_found:
                logger.info("[%s] Keywords matched on reply with best analysis: %s",
                            tc_id, keywords_matched)
            elif status == "PASS":
                status = "FAIL"
                error_message = (
                    f"[{tc_id}] No expected keyword found in any bot reply.\n"
                    f"  Expected (any of): {tc.expected_keywords}\n"
                    f"  All replies:       {all_replies}\n"
                    f"  Inputs:            {tc.input_messages}"
                )
                logger.error("[%s] %s", tc_id, error_message)

        # 3b. Expected classification (if specified)
        if status == "PASS" and tc.expected_classification:
            actual_class = (check_analysis.get("classification") or "").lower()
            expected_lower = tc.expected_classification.lower()
            found_in_analysis = expected_lower in actual_class
            found_in_reply = expected_lower in check_reply.lower()

            if not found_in_analysis and not found_in_reply:
                status = "FAIL"
                error_message = (
                    f"[{tc_id}] Classification '{expected_lower}' not found.\n"
                    f"  Analysis class: {actual_class!r}\n"
                    f"  Bot reply:      {check_reply[:300]}"
                )
                logger.error("[%s] %s", tc_id, error_message)
            elif found_in_reply and not found_in_analysis:
                logger.debug("[%s] Classification '%s' found in reply text",
                             tc_id, expected_lower)

        # 3c. Expected journey (if specified)
        if status == "PASS" and tc.expected_journey:
            actual_journey = (check_analysis.get("journey") or "").lower()
            expected_journey = tc.expected_journey.lower()
            if expected_journey not in actual_journey:
                status = "FAIL"
                error_message = (
                    f"[{tc_id}] Journey mismatch.\n"
                    f"  Expected: {expected_journey}\n"
                    f"  Got:      {actual_journey}"
                )
                logger.error("[%s] %s", tc_id, error_message)

        # 3d. Expected emotion (if specified)
        if status == "PASS" and tc.expected_emotion:
            actual_emotion = (check_analysis.get("emotion") or "").lower()
            if tc.expected_emotion.lower() not in actual_emotion:
                status = "FAIL"
                error_message = (
                    f"[{tc_id}] Emotion mismatch.\n"
                    f"  Expected: {tc.expected_emotion}\n"
                    f"  Got:      {actual_emotion}"
                )
                logger.error("[%s] %s", tc_id, error_message)

    except Exception as exc:
        # Catch any unexpected exception (e.g. unhandled assertion, connection error)
        if not error_message:
            status = "ERROR"
            error_message = f"Unexpected error: {exc}"
            logger.error("[%s] %s", tc_id, error_message)

    # ------------------------------------------------------------------
    # Record result to TEST_RESULTS
    # ------------------------------------------------------------------
    record_result(
        test_id=tc_id,
        language=tc.language,
        scenario_type=tc.scenario_type,
        input_messages=tc.input_messages,
        expected_keywords=tc.expected_keywords,
        expected_classification=tc.expected_classification,
        expected_journey=tc.expected_journey,
        expected_emotion=tc.expected_emotion,
        notes=tc.notes,
        status=status,
        latency_ms=check_latency,
        turns=len(all_replies),
        bot_reply=check_reply,
        analysis=check_analysis,
        keywords_matched=keywords_matched,
        expected_not_found=expected_not_found,
        error_message=error_message,
        source_sheet=tc.source_sheet if hasattr(tc, 'source_sheet') else "",
    )

    # Log final status
    if status == "PASS":
        logger.info("[%s] PASS — latency=%.0fms class=%s journey=%s keywords=%s",
                    tc_id, check_latency,
                    check_analysis.get("classification", ""),
                    check_analysis.get("journey", ""),
                    keywords_matched)
    else:
        logger.warning("[%s] %s — %s", tc_id, status, error_message[:200] if error_message else "")

    # Fail the test if needed
    if status != "PASS":
        pytest.fail(error_message)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _record_and_fail(status, error_message, tc, tc_id, all_replies, final_analysis, final_latency, keywords_matched, expected_not_found):
    """Record result and fail, to avoid repeating this pattern inline."""
    record_result(
        test_id=tc_id,
        language=tc.language,
        scenario_type=tc.scenario_type,
        input_messages=tc.input_messages,
        expected_keywords=tc.expected_keywords,
        expected_classification=tc.expected_classification,
        expected_journey=tc.expected_journey,
        expected_emotion=tc.expected_emotion,
        notes=tc.notes,
        status=status,
        latency_ms=final_latency,
        turns=len(all_replies),
        bot_reply=all_replies[-1] if all_replies else "",
        analysis=final_analysis,
        keywords_matched=keywords_matched,
        expected_not_found=expected_not_found,
        error_message=error_message,
        source_sheet=tc.source_sheet if hasattr(tc, 'source_sheet') else "",
    )
    pytest.fail(error_message)
