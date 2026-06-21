# Product Requirements Document — **Claude**, a Voice-First AI Agent

**Author:** Daniel
**Status:** Draft v1.0
**Last updated:** 2026-06-21
**Codename:** Claude (voice persona — British accent, warm and witty)

---

## 1. Overview

**Claude** is a voice-first, personal AI agent that lives on your local machine and acts
as a capable, trustworthy chief-of-staff. You speak to her naturally; she listens,
thinks, takes action, and speaks back in a warm British accent. Over time she gains
secure, permissioned access to your calendar, email, payment systems (Stripe), the web,
and your local files — so she can not only *answer* questions but *do the work*.

The north star: **reduce the friction between an intention you say out loud and the action
being completed correctly, safely, and with your confirmation when it matters.**

### One-line pitch
> "Talk to Claude like you'd talk to the sharpest assistant you've ever hired — she
> remembers, she researches, she acts, and she never does anything risky without asking."

---

## 2. Goals & Non-Goals

### 2.1 Goals
1. **Voice-first interaction** — fluid, low-latency, barge-in capable spoken conversation.
2. **Agentic action-taking** — read *and* write across connected tools (calendar, email,
   Stripe, files), not just chat.
3. **Local-first footprint** — the UI and orchestration run on the user's machine; the
   user owns their data and decides what leaves the device.
4. **Trustworthy by design** — explicit consent, previews before irreversible actions,
   full audit log, and a hard "undo / stop" at all times.
5. **Web-grounded answers** — fetch and synthesize live information from the internet with
   citations.
6. **Distinct persona** — a consistent British-accented voice and personality the user
   enjoys talking to, including a free-flowing "discuss a topic with me" conversation mode.

### 2.2 Non-Goals (v1)
- Multi-user / team accounts (single-owner only in v1).
- Mobile-native apps (desktop-first; mobile is a later phase).
- Autonomous financial transactions without confirmation (always human-in-the-loop for
  money movement).
- Acting on connected accounts while the user is fully offline/unattended (v1 keeps a human
  in the loop for sensitive writes).

---

## 3. Target User & Personas

**Primary user: "The Operator" (Daniel)** — a founder/operator juggling calendar, inbox,
payments, research, and documents. Wants leverage, hates context-switching, types less than
he talks, and cares deeply about privacy and control.

| Need | How Claude serves it |
|------|----------------------|
| "Stop me drowning in my inbox" | Triage, summarize, draft replies for approval |
| "Protect my calendar" | Schedule, reschedule, defend focus blocks |
| "Tell me what's going on with revenue" | Read Stripe, summarize MRR, refunds, failed payments |
| "Find me the answer, fast" | Web research with sources |
| "Organize my files" | Rename, move, summarize, draft, and edit documents locally |
| "Just let me think out loud" | Conversation mode — debate, brainstorm, rubber-duck |

---

## 4. Experience Principles

1. **Speak first, screen second.** Voice is the primary modality; the UI is the receipt,
   the control panel, and the safety net.
2. **Always interruptible.** The user can talk over Claude (barge-in) and say "stop" at any
   moment — speech halts, any in-flight action pauses.
3. **Show your work.** Every action and every web claim is traceable in the activity log.
4. **Confirm what's costly.** Reversible/cheap actions can be auto-run; irreversible or
   money/identity-affecting actions require explicit confirmation.
5. **Earn trust incrementally.** Permissions are granted per-integration, per-scope, and can
   be tightened or revoked at any time.

---

## 5. Core Capabilities (Functional Requirements)

### 5.1 Voice interaction
- **FR-V1** Wake word ("Hey Claude") and/or push-to-talk hotkey to start listening.
- **FR-V2** Streaming speech-to-text (STT) with partial transcripts shown live.
- **FR-V3** Streaming text-to-speech (TTS) in a configurable British accent voice.
- **FR-V4** Barge-in: user speech interrupts Claude's speech within ~200ms.
- **FR-V5** "Stop" / "cancel" / "never mind" halts speech and aborts the current action.
- **FR-V6** Voice activity detection + end-of-utterance detection so the user needn't press
  a button to "finish."
- **FR-V7** Whisper/quiet mode and text fallback for situations where speaking aloud is
  awkward.

### 5.2 Conversation / "discuss a topic" mode
- **FR-C1** A dedicated mode where Claude holds an open-ended spoken dialogue: debate a
  topic, brainstorm, role-play an interviewer, or act as a sounding board.
- **FR-C2** Maintains conversational memory within the session and references earlier points.
- **FR-C3** Configurable stance: "steelman the other side," "play devil's advocate,"
  "Socratic questioning," "just brainstorm with me."
- **FR-C4** Natural turn-taking with backchannel cues ("mm-hm", "right") optional.
- **FR-C5** Can pull in live web facts mid-discussion when asked ("look that up").
- *(See companion prototype in `/prototype` for a runnable starting point.)*

### 5.3 Calendar integration
- **FR-CAL1** Read events, free/busy, and reminders.
- **FR-CAL2** Create / move / cancel events (with confirmation for events involving others).
- **FR-CAL3** "Find time" across constraints ("30 min with Sam next week, mornings only").
- **FR-CAL4** Defend focus blocks and detect conflicts/double-bookings.
- **FR-CAL5** Time-zone aware; always speaks times in the user's local zone unless told.

### 5.4 Email integration
- **FR-EM1** Read, search, and summarize inbox / threads.
- **FR-EM2** Draft replies and new messages — **never auto-send without confirmation in v1.**
- **FR-EM3** Triage: label, archive, flag, surface "needs reply" and "waiting on."
- **FR-EM4** Extract action items and offer to add them to calendar/tasks.
- **FR-EM5** Detect and flag suspected phishing / unusual requests before acting.

### 5.5 Payments (Stripe) integration
- **FR-ST1** Read-only first: MRR, revenue, recent charges, refunds, failed payments,
  disputes, churn.
- **FR-ST2** Spoken financial summaries ("How did we do this week?").
- **FR-ST3** Write actions (issue refund, send invoice, cancel subscription) are **gated
  behind explicit confirmation + a typed/spoken amount read-back** ("Refund £240 to
  Acme — say 'confirm' to proceed").
- **FR-ST4** Hard limits: per-action and daily ceilings the user configures; anything above
  requires re-authentication.
- **FR-ST5** Operate against Stripe **test mode** by default until the user explicitly
  switches to live.

### 5.6 Local machine, files & documents
- **FR-FS1** Browse, search, read, summarize files within user-approved directories only.
- **FR-FS2** Create, edit, rename, move, and organize files/folders.
- **FR-FS3** Document editing: draft, rewrite, format, and revise documents on disk.
- **FR-FS4** A **scoped workspace**: Claude can only touch explicitly allow-listed paths;
  everything else is invisible to her.
- **FR-FS5** Every write produces a diff/preview and a recoverable backup (trash, not
  permanent delete) so changes are reversible.
- **FR-FS6** Never execute arbitrary shell/code without explicit, per-command approval.

### 5.7 Web research
- **FR-W1** Search the web and fetch page contents to answer questions.
- **FR-W2** Synthesize across multiple sources and **cite them** (spoken: "according to
  three sources…"; on-screen: clickable links).
- **FR-W3** Distinguish fact from inference and flag uncertainty / conflicting sources.
- **FR-W4** Respect robots/paywalls; degrade gracefully when content is inaccessible.
- **FR-W5** Cache results within a session to avoid redundant fetching.

### 5.8 Memory & personalization
- **FR-M1** Long-term memory of preferences, people, projects, and recurring tasks —
  stored **locally**, user-inspectable and user-editable.
- **FR-M2** "Forget that" / memory wipe controls.
- **FR-M3** Learns the user's writing voice for drafting emails/docs.

### 5.9 UI / control surface (local)
- **FR-UI1** A persistent local app window: live transcript, current action, activity log.
- **FR-UI2** Integration manager: connect/disconnect, view granted scopes, revoke.
- **FR-UI3** Permission & limits settings (auto-run thresholds, spend caps, allow-listed dirs).
- **FR-UI4** Voice settings: accent, speaking rate, wake word, push-to-talk key.
- **FR-UI5** Global "STOP" button and a session "panic / disconnect everything" control.
- **FR-UI6** Audit log export.

---

## 6. The Persona: voice & personality

- **Accent & voice:** British English (RP-leaning by default; selectable variants). Warm,
  composed, quick-witted, never sycophantic.
- **Tone:** Competent and concise by default; can shift to playful in conversation mode.
- **Speech style:** Short sentences for actions ("Done. Moved it to 3pm."), richer prose
  for discussion. Speaks numbers/money clearly and reads back critical details.
- **Boundaries in persona:** Stays helpful and honest; declines unsafe requests plainly;
  never pretends to have done something it hasn't.
- **Configurable:** rate, pitch, formality, verbosity, and "how much personality" slider.

---

## 7. System Architecture (high level)

```
┌──────────────────────────── Local Machine ─────────────────────────────┐
│                                                                          │
│   ┌─────────────┐    audio    ┌──────────────┐    text    ┌──────────┐  │
│   │  Mic / VAD  │ ──────────▶ │  STT (stream) │ ─────────▶ │  Agent   │  │
│   └─────────────┘             └──────────────┘            │  Core /   │  │
│   ┌─────────────┐    audio    ┌──────────────┐    text    │  Planner  │  │
│   │  Speaker    │ ◀────────── │  TTS (stream) │ ◀───────── │ (LLM)     │  │
│   └─────────────┘             └──────────────┘            └────┬─────┘  │
│                                                                 │        │
│   ┌──────────────┐   ┌───────────────┐   ┌─────────────┐        │        │
│   │ Local UI app │   │ Memory store  │   │ Audit log   │ ◀──────┤        │
│   │ (Electron/   │   │ (local DB)    │   │ (append-only)│        │        │
│   │  Tauri)      │   └───────────────┘   └─────────────┘        │        │
│   └──────────────┘                                              │        │
│                                                                 ▼        │
│   ┌──────────── Tool / Integration Layer (MCP-style) ───────────────┐    │
│   │  Calendar │ Email │ Stripe │ Filesystem │ Web fetch │ …          │    │
│   │  (OAuth tokens in OS keychain; scoped; revocable)               │    │
│   └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
        │ outbound only, per-integration, user-consented
        ▼
   External APIs (Google/Microsoft, Stripe, the web, LLM provider)
```

**Key choices**
- **Local orchestration** (Electron or Tauri shell + a local agent process). The UI and the
  planner run on-device; only the specific data needed for a task is sent to external APIs.
- **Tool layer modeled as discrete, permissioned tools** (an MCP-style contract) so new
  integrations are pluggable and each has its own scopes and limits.
- **Secrets in the OS keychain** (Keychain / Credential Manager / libsecret) — never in
  plaintext config.
- **Streaming everywhere** (STT, LLM, TTS) to keep voice latency low.
- **LLM:** use the latest, most capable Claude models for the agent core (planning,
  tool-use, conversation). Keep the model provider behind an interface so it's swappable.

---

## 8. Safety, Security & Privacy (first-class, not an afterthought)

### 8.1 Consent & permissions
- Per-integration OAuth with the **narrowest scopes** that work; show the user exactly what
  was granted.
- **Action tiers:**
  - **Tier 0 – Read/observe:** auto-allowed once integration is connected.
  - **Tier 1 – Reversible writes** (draft email, create internal file, tentative calendar
    hold): auto-run allowed if user opted in; otherwise quick confirm.
  - **Tier 2 – External/irreversible** (send email, invite others, move money, delete
    files): **always explicit confirmation with read-back.**
- Spend caps and per-action ceilings for Stripe; allow-listed directories for the filesystem.

### 8.2 Auditability & recovery
- Append-only **audit log** of every tool call (inputs, result, timestamp).
- **Undo** for everything reversible; **soft-delete / trash** instead of hard delete.
- "What did you just do?" — Claude can narrate her last N actions on request.

### 8.3 Data handling
- Local-first storage; explicit indication whenever data leaves the device.
- Redaction of secrets/PII from logs and from anything sent to the web-research path.
- Clear data-retention controls and a one-click "wipe local memory."

### 8.4 Abuse / injection defenses
- **Prompt-injection hardening:** content fetched from web pages or emails is treated as
  *untrusted data*, never as instructions. Claude does not execute commands found in fetched
  content without the user's direct say-so.
- Phishing/scam detection on inbound email before any action.
- Rate limiting and anomaly detection on sensitive tools.
- Authentication step-up (re-auth / biometric) before Tier 2 financial actions.

---

## 9. Edge Cases (the part that makes it real)

### Voice & audio
- Background noise, crosstalk, multiple speakers → confidence scoring; ask to repeat.
- Misheard wake word / accidental activation → confirmation before any Tier 1+ action.
- Mishearing a critical value (amounts, dates, names) → **always read back and confirm.**
- Homophones ("to/two/too", "Sam/Sandra") → disambiguate by asking.
- User talks over Claude → barge-in stops speech cleanly mid-word.
- Long silence after wake → time out and stand down gracefully.
- Speaking the wrong currency / time-zone → normalize and confirm.

### Calendar
- Double-booking & conflicting invites → flag, propose alternatives, never silently overwrite.
- Recurring-event edits ("this one" vs "all future") → must ask which.
- Cross-time-zone meetings → state both zones.
- Declined/ tentative responses → reflect status, don't assume attendance.

### Email
- Ambiguous "reply to John" when three Johns exist → disambiguate.
- Draft references attachments that don't exist → catch before send.
- "Send it" said casually → still confirm recipients + subject (read-back) for external mail.
- Auto-replies / loops → detect and avoid creating mail storms.
- Sensitive content (legal, HR, medical) → extra confirmation, suggest caution.

### Stripe / payments
- Refund amount exceeds original charge → block.
- Currency mismatch → block + clarify.
- Duplicate refund (same charge twice) → detect and warn.
- Live vs test mode confusion → loud, persistent indicator of which mode is active.
- Network failure mid-transaction → never assume success; reconcile against Stripe, report
  true state.
- Dispute/chargeback in flight → warn before issuing related refunds.

### Filesystem / documents
- Path outside the allow-list → refuse and explain.
- File open/locked by another app → don't corrupt; queue or report.
- Name collisions on move/rename → ask or auto-suffix, never silently overwrite.
- "Delete the file" → trash, confirm, recoverable.
- Huge files / binary files → handle gracefully, don't try to "read" a 2GB binary aloud.
- Encoding issues / merge conflicts in edited docs → preserve original, show diff.
- Concurrent edit by the user while Claude edits → detect change, re-sync, avoid clobber.

### Web research
- Conflicting sources → present the disagreement, don't fabricate consensus.
- Paywalled / blocked content → say so, find alternatives.
- Outdated info → note recency; prefer dated sources for time-sensitive facts.
- No good answer exists → say "I don't know / couldn't verify" rather than guess.
- Malicious page trying to inject instructions → ignore as data (see §8.4).

### System / connectivity
- Internet drops mid-task → pause, preserve state, resume or report partial completion.
- LLM/API outage → degrade to local-only capabilities; tell the user.
- Token/credential expiry → prompt re-auth, don't fail silently.
- Two requests at once ("also, while you're at it…") → queue and manage a task list.
- Conflicting instructions ("cancel that — no, keep it") → confirm final intent.
- Power loss / crash mid-write → journaled writes + backups so nothing is half-written.

### Trust & ambiguity
- Vague command ("sort out my morning") → ask a clarifying question before acting.
- Action the user might regret (email the whole company) → extra-strong confirmation.
- Claude is uncertain → expresses calibrated confidence, offers to verify.

---

## 10. Non-Functional Requirements

| Area | Target |
|------|--------|
| Voice latency (end of speech → start of reply) | < 1.0s typical; < 1.5s with web/tool use start |
| STT word error rate (clear speech) | Low enough for reliable command capture; critical values always confirmed |
| Barge-in stop time | < 200ms |
| Availability of local UI | Runs offline for local-only features; network only for connected tools |
| Security | Secrets in OS keychain; least-privilege scopes; encrypted local store |
| Recoverability | All Tier-1/2 actions reversible or confirmable |
| Privacy | No data leaves device without an explicit, logged reason |
| Accessibility | Full text fallback; captions for all spoken output; keyboard control |

---

## 11. Success Metrics

- **Activation:** user connects ≥2 integrations in week 1.
- **Engagement:** daily voice sessions; tasks completed by voice / day.
- **Trust:** ratio of actions auto-approved vs corrected; near-zero "unwanted action" events.
- **Time saved:** self-reported and inferred (emails triaged, meetings scheduled hands-free).
- **Quality:** % of web answers the user rates accurate; draft-email accept-without-edit rate.
- **Safety:** 0 unauthorized Tier-2 actions; 100% of money/identity actions confirmed.

---

## 12. Roadmap (phased)

**Phase 0 — Voice loop + conversation (Weeks 1–3)**
Wake word, STT→LLM→TTS streaming, British voice, barge-in, and the "discuss a topic" mode.
Local UI shell with transcript + STOP. *(Prototype in `/prototype` seeds this.)*

**Phase 1 — Local files + web research (Weeks 4–7)**
Scoped filesystem (read/edit/organize with diffs & trash), web search/fetch with citations,
local memory store, audit log.

**Phase 2 — Calendar + email, read-first (Weeks 8–11)**
Read/summarize/triage; draft (no auto-send); find-time; action-item extraction.

**Phase 3 — Stripe read + gated writes (Weeks 12–15)**
Read-only financial summaries; refunds/invoices behind confirmation + read-back + caps;
test-mode default.

**Phase 4 — Hardening & polish (Weeks 16+)**
Injection defenses, step-up auth, anomaly detection, accessibility pass, performance tuning,
broader integrations ("and more": tasks, notes, Slack, browser control).

---

## 13. Open Questions
1. Preferred TTS/STT providers (cloud quality vs on-device privacy) — pick per-tier?
2. Electron vs Tauri for the shell (bundle size & native perf vs ecosystem)?
3. How autonomous should Tier-1 be by default — opt-in or opt-out auto-run?
4. Which calendar/email backend first (Google vs Microsoft)?
5. Wake word: on-device model vs push-to-talk only for v0?

---

## 14. Appendix — Glossary
- **Barge-in:** interrupting the agent's speech by talking.
- **Tier 0/1/2:** action-risk levels governing how much confirmation is required.
- **Read-back:** Claude repeats critical details (amount, recipient, date) before committing.
- **Scoped workspace:** the explicit allow-list of directories Claude may touch.
- **MCP-style tool layer:** discrete, permissioned tools the agent calls, each with its own
  scopes/limits.
