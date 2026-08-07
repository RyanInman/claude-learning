# Complexity Report: PaymentService.cs

File: `/Users/admin/claude-learning/skills/analyzing-code-complexity/evals/files/PaymentService.cs`

Metrics: cyclomatic complexity per McCabe (1 + decision points), cognitive complexity per SonarSource spec (increments for control-flow breaks, +1 per nesting level for nested structures, flat +1 for `switch` regardless of case count).

## Summary

| Method | Lines | Cyclomatic | Cognitive |
|---|---|---|---|
| `StatusLabel(int)` | 8-19 | 6 | 1 |
| `Charge(Order)` | 21-36 | 3 | 2 |
| `Discount(Customer)` | 38-41 | 3 | 2 |
| `Process(List<Order>)` | 43-62 | 6 | 12 |
| `Retry(Order)` | 64 | 1 | 0 |
| `Log(Exception)` | 65 | 1 | 0 |
| `Ship(Item)` | 66 | 1 | 0 |
| `Notify(Order, Item)` | 67 | 1 | 0 |
| **Class total** | | **22** | **17** |

## Per-Method Breakdown

### StatusLabel — cyclomatic 6, cognitive 1

Cyclomatic: base 1 + 5 `case` labels (`default` adds nothing) = 6.

Cognitive: `switch` counts +1 total, regardless of case count = 1.

Largest divergence in the file. Flat switch-to-return mapping is trivially readable despite 6 execution paths. Cyclomatic overstates its difficulty; cognitive captures reality.

### Charge — cyclomatic 3, cognitive 2

Cyclomatic: base 1 + 2 `catch` clauses = 3.

Cognitive: `catch (TimeoutException)` +1, `catch (GatewayException)` +1 = 2. Both at nesting 0, no nesting penalty; `try` and rethrow add nothing.

### Discount — cyclomatic 3, cognitive 2

Cyclomatic: base 1 + ternary `?:` + `&&` = 3.

Cognitive: ternary +1, `&&` operator sequence +1 = 2.

### Process — cyclomatic 6, cognitive 12

Cyclomatic: base 1 + outer `foreach` + `if (o.Paid)` + inner `foreach` + `if (i.InStock || i.Backorderable)` + `||` = 6.

Cognitive, structure-by-structure (increment = 1 + nesting depth):

| Construct | Nesting depth | Increment |
|---|---|---|
| outer `foreach` (line 45) | 0 | +1 |
| `if (o.Paid)` (line 47) | 1 | +2 |
| inner `foreach` (line 49) | 2 | +3 |
| `if (...)` (line 51) | 3 | +4 |
| `\|\|` sequence (line 51) | — | +1 |
| `else` (line 55) | — | +1 |
| **Total** | | **12** |

### Retry, Log, Ship, Notify — cyclomatic 1, cognitive 0

Single-path bodies, no branching.

## Findings

1. **StatusLabel vs Process: identical cyclomatic (6), 12x cognitive gap (1 vs 12).** Cyclomatic counts paths; cognitive weights nesting. A flat switch and a 4-deep nested loop score the same on cyclomatic while differing drastically in mental load. Rank refactoring candidates by cognitive, not cyclomatic.

2. **Process is the only method worth refactoring.** Cognitive 12 approaches the Sonar default threshold (15); many teams flag at 10. Two cheap fixes:
   - Guard clause: `if (!o.Paid) continue;` removes one nesting level (cognitive 12 -> 9).
   - Extract inner loop to `ShipOrder(Order o)`: resets nesting in the extracted method (roughly 12 -> 4 + 3 split).

3. **StatusLabel needs no change** despite its cyclomatic score. If style demands, a C# switch expression or `Dictionary<int, string>` reduces cyclomatic to 1-2 without readability cost.

4. Remaining methods are trivial; no action needed.
