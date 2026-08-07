# Complexity Report: PaymentService.cs

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| PaymentService.StatusLabel | 6 | 1 | ✅ |
| PaymentService.Charge | 3 | 2 | ✅ |
| PaymentService.Discount | 3 | 2 | ✅ |
| PaymentService.Process | 6 | 12 | ✅ |
| PaymentService.Retry | 1 | 0 | ✅ |
| PaymentService.Log | 1 | 0 | ✅ |
| PaymentService.Ship | 1 | 0 | ✅ |
| PaymentService.Notify | 1 | 0 | ✅ |

## PaymentService.Process

**Cyclomatic: 6** — base 1 + 2 foreach + 2 if + 1 `||`
**Cognitive: 12** — 2 foreach + 2 if + 1 `||` + 1 else (= 6) + nesting penalties (+1, +2, +3)

Sharpest divergence in the file: only 6 test paths, but 12 cognitive because every structure sits inside the previous one — four levels deep by the innermost `if`. The nesting penalties (half the score) are what a reader feels, not the branch count.

```csharp
foreach (var o in orders)                    // Cog +1
    if (o.Paid)                              // Cog +1, nesting +1
        foreach (var i in o.Items)           // Cog +1, nesting +2
            if (i.InStock || i.Backorderable)// Cog +1, nesting +3, || +1
                Ship(i);
            else                             // Cog +1
                Notify(o, i);
```

Cheap fix: extract the inner loop into `ShipOrder(Order o)`. Process drops to cognitive 3 (foreach + if + nesting 1) and ShipOrder scores 5 (foreach + if + || + else + nesting 1) — same behavior, 12 → 3+5 split across two shallow units.

## PaymentService.Charge

**Cyclomatic: 3** — base 1 + 2 catch
**Cognitive: 2** — 2 catch, no nesting penalties

Two exception paths plus the happy path; each catch is a distinct behavior (retry vs log-and-rethrow) so three test cases are genuinely needed. Both catches sit at top level, so cognitive stays low — easy to read, moderately branchy to test.

## PaymentService.Discount

**Cyclomatic: 3** — base 1 + 1 ternary + 1 `&&`
**Cognitive: 2** — 1 ternary + 1 `&&`, no nesting

One condition with a compound predicate. Both metrics agree it is trivial; a single-expression ternary at top level carries no nesting cost.

## PaymentService.StatusLabel

**Cyclomatic: 6** — base 1 + 5 case (default not counted)
**Cognitive: 1** — the switch itself; cases are free

Classic switch divergence, opposite direction from Process: cyclomatic charges per case (6 paths to test) while cognitive charges +1 for the whole switch. A flat mapping switch like this is many-test-paths but near-zero reading cost — not a refactor candidate. Each case body is a bare return with no logic.

---

*Convention note: this report counts each `&&`/`||` operator (+1 each) for both metrics. SonarQube's cognitive-complexity spec counts a run of like operators as +1 total, so its numbers may read slightly lower.*
