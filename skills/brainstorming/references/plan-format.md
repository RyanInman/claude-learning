# Plan format

Read this when the interview ends and you are ready to present the plan. Follow the template exactly, because a plan that looks the same on run 50 as on run 1 is the reason the user reached for this skill.

## Contents

- [Template](#template)
- [EARS syntax](#ears-syntax)
- [Naming real things](#naming-real-things)
- [Build order](#build-order)
- [Filled example](#filled-example)

---

## Template

Present in the conversation. Do not write a file unless the user asks.

```
## Outcome

[One paragraph, present tense, written as though the change shipped. State what
a user can now do that they could not do before. No implementation detail.]

## Requirements

**Must**
- [EARS sentence]
- [EARS sentence]

**Should**
- [EARS sentence]

**Could**
- [EARS sentence]

**Won't (this round)**
- [Plain sentence]

## Acceptance criteria

**[Must requirement 1]**
- Given [starting state]
- When [action]
- Then [observable result]

**[Must requirement 2]**
- Given ...
- When ...
- Then ...

## Non-functional requirements

- [Constraint that changes the design, with its number]

## Build order

1. [Step] — touches `[file]`, `[file]`. Verify: [check that proves it worked]
2. [Step] — touches `[file]`. Verify: [check]
3. [Step] — touches `[file]`. Verify: [check]

## Assumptions and open questions

- CONFIRMED — [fact the user stated]
- ASSUMED — [fact you filled in]. [What changes if wrong.]
- OPEN — [question still unanswered]. [How you are proceeding meanwhile.]

## Out of scope

- [Thing you are deliberately not building, and why]
```

Close with one line asking the user to approve, correct, or cut.

## Naming real things

A requirement that names no file, table, endpoint, or symbol cannot be tested and cannot be built from. "The system shall aggregate the main transactional record" tells a reader nothing they did not already know.

Read the schema and the routes, then use the real names. Where you cannot find one, write your best guess and mark it ASSUMED, because a named guess is correctable and a generic noun is not.

| Instead of | Write |
|---|---|
| the main transactional record | the `orders` table |
| the reporting endpoint | `GET /api/admin/reports/summary` |
| the relevant middleware | `src/middleware/rateLimit.ts` |
| records per day | `orders` grouped by `created_at::date` |

## Build order

The user approves a plan to find out what it costs and where they can cut. A plan with no order gives them nothing to cut, so sequence the work before you present it.

- **Number the steps and name the files each one touches.** A step that names no file is a wish.
- **Give every step a verification** — a command, a test, a thing to look at. Reason: a step nobody can check is a step nobody can hand off.
- **Order so the user can stop early.** Each step should leave something that runs. When the payoff only lands at the final step, the user cannot trade scope for time once the estimate arrives.
- **Put the riskiest unknown first** where the order allows, because finding out in step 2 that the approach fails is far cheaper than finding out in step 8.

## EARS syntax

Five patterns. Pick the one that matches the trigger condition, because a requirement without its condition is untestable.

| Pattern | Shape | Use when |
|---|---|---|
| Ubiquitous | The «system» shall «response». | Always true |
| Event-driven | When «trigger», the «system» shall «response». | A discrete event fires it |
| State-driven | While «state», the «system» shall «response». | True throughout a state |
| Unwanted | If «condition», then the «system» shall «response». | Error and edge handling |
| Optional | Where «feature included», the «system» shall «response». | Behind a flag or tier |

Combine conditions front to back: "While the order is pending, when the payment gateway returns a decline, the system shall mark the order failed."

Keep one requirement per sentence. A requirement containing "and" is two requirements and will be tested as one.

## Filled example

From the notification request in the SKILL.md worked example.

```
## Outcome

An on-call engineer learns about a failed order within seconds, without watching
a dashboard. Every order that fails for any reason raises a Slack alert to the
on-call channel carrying enough detail to start work: order id, customer,
failure reason, and a link to the order in the admin.

## Requirements

**Must**
- When an order transitions to the failed state, the system shall post an alert
  to the configured Slack channel within 30 seconds.
- The alert shall carry the order id, the customer email, the failure reason,
  and a link to the order in the admin.
- If the Slack API call fails, then the system shall retry twice with backoff.
- If all three Slack attempts fail, then the system shall write an error-level
  log entry naming the order id.

**Should**
- Where more than 10 orders fail within 5 minutes, the system shall post one
  grouped alert instead of 10 separate alerts.

**Could**
- The alert shall carry a button that marks the order as being worked on.

**Won't (this round)**
- Email or SMS delivery.
- A customer-facing notification.

## Acceptance criteria

**Alert on failure**
- Given an order in the pending state
- When the payment gateway returns a decline and the order moves to failed
- Then a message appears in the on-call Slack channel within 30 seconds

**Retry on Slack outage**
- Given the Slack API is returning 503
- When an order fails
- Then the system attempts the post three times, then logs an error naming the
  order id

## Non-functional requirements

- Alert latency under 30 seconds at the 95th percentile.
- The Slack webhook URL is read from configuration, never committed.

## Build order

1. Add the failed-order hook — touches `src/orders/stateMachine.ts`. Verify: a unit test asserting the hook fires once on the pending-to-failed transition.
2. Build the alert payload and formatter — touches `src/alerts/orderFailed.ts`. Verify: a snapshot test of the formatted message for one fixture order.
3. Wire the Slack client with retry and backoff — touches `src/alerts/slackClient.ts`, `src/config.ts`. Verify: a test with a stubbed 503 confirms three attempts, then an error log naming the order id.
4. Ship behind `ALERTS_ENABLED`, default off — touches `src/config.ts`. Verify: staging order fails, message lands in the test channel.
5. Turn it on in production. Verify: watch the channel through one real failure.
6. Add the 10-in-5-minutes grouping — touches `src/alerts/orderFailed.ts`. Verify: a test firing 12 failures produces one message.

Steps 1-5 ship a working alert. Step 6 is the Should requirement and can be dropped without touching what came before.

## Assumptions and open questions

- CONFIRMED — recipient is the on-call engineer, not the ops dashboard.
- CONFIRMED — every failure type counts, not payment declines alone.
- ASSUMED — Slack is the channel. If the team uses Teams, the delivery module
  changes; the trigger and payload do not.
- ASSUMED — the existing order state machine already emits a failed transition.
  If it does not, add roughly a day to wire the hook.
- OPEN — which channel. Proceeding with a configurable channel id, defaulted to
  #ops-alerts.

## Out of scope

- Alert routing rules per failure type. One channel this round; routing is a
  second feature once we see the volume.
```
