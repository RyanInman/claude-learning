# Scoring Rules — Detail, Edge Cases, Worked Examples

Conventions this skill uses. Tool implementations (SonarQube, linters) differ in small ways; when the user's tooling matters, note the variance in the report rather than silently switching conventions.

## Contents
- [Pinned conventions](#pinned-conventions)
- [Worked examples](#worked-examples)
- [Edge cases](#edge-cases)
- [Thresholds and rationale](#thresholds-and-rationale)

## Pinned conventions

| Construct | Cyclomatic | Cognitive |
|-----------|-----------|-----------|
| `if` / `else if` | +1 | +1 (+nesting) |
| `else` | 0 | +1 (no nesting penalty) |
| loop (`for`, `while`, `do`, `foreach`) | +1 | +1 (+nesting) |
| `case` in switch | +1 each | 0 |
| switch/match statement itself | 0 | +1 (+nesting) |
| `default` | 0 | 0 |
| `&&`, `||` | +1 each | +1 each (no nesting penalty) |
| ternary `?:` | +1 | +1 (+nesting) |
| `catch` | +1 each | +1 each (+nesting) |
| `finally` | 0 | 0 |
| guard clause / early `return` | 0 | 0 |
| `break`/`continue` to label, `goto` | 0 | +1 |
| direct recursion | 0 | +1 |
| null-coalescing (`??`, `?.` chains) | 0 | 0 |

Variance note: SonarSource's cognitive spec counts a *sequence* of like boolean operators (`a && b && c`) as +1 total; the guide article this skill follows counts each operator (+2 there). This skill counts **each operator** for both metrics — simpler, consistent across the two scores. Flag this in the report if the user compares against SonarQube numbers.

## Worked examples

### Guard clauses vs nesting — same cyclomatic, different cognitive

```csharp
// Nested version
bool CanShip(Order o) {
    if (o != null) {                 // CC +1 | Cog +1
        if (o.Items.Any()) {         // CC +1 | Cog +1, nesting +1
            if (o.Paid) {            // CC +1 | Cog +1, nesting +2
                return true;
            }
        }
    }
    return false;
}
// Cyclomatic: 1 + 3 = 4    Cognitive: 3 + 3 = 6
```

```csharp
// Guard-clause version — identical behavior
bool CanShip(Order o) {
    if (o == null) return false;     // CC +1 | Cog +1
    if (!o.Items.Any()) return false;// CC +1 | Cog +1
    if (!o.Paid) return false;       // CC +1 | Cog +1
    return true;
}
// Cyclomatic: 1 + 3 = 4    Cognitive: 3
```

Same decisions, same paths, same cyclomatic — cognitive halves. This pair is the canonical divergence example; reuse its shape in reports.

### Switch — divergence the other way

```csharp
string Label(int code) {
    switch (code) {              // Cog +1
        case 1: return "one";    // CC +1
        case 2: return "two";    // CC +1
        case 3: return "three";  // CC +1
        default: return "other";
    }
}
// Cyclomatic: 1 + 3 = 4    Cognitive: 1
```

High case-count switches inflate cyclomatic while staying easy to read. Report them as "many test paths, low reading cost" — not refactor candidates unless cases contain logic.

### Boolean operators

```python
def eligible(u):
    if u.active and u.verified and not u.banned:  # CC: +1 if, +2 and | Cog: +1 if, +2 and
        return True
    return False
# Cyclomatic: 1 + 3 = 4    Cognitive: 3
```

### Loop with nested condition

```python
def first_error(rows):
    for r in rows:               # CC +1 | Cog +1
        if r.status == "error":  # CC +1 | Cog +1, nesting +1
            return r
    return None
# Cyclomatic: 3    Cognitive: 3
```

## Edge cases

**Lambdas / anonymous functions / closures**: their contents count toward the enclosing method's scores. For cognitive, a lambda adds one nesting depth for structures inside it but does not itself increment. A branching lambda inside a loop therefore gets loop-depth + lambda-depth penalties.

**Nested local functions**: score a named local function as its own unit. List it as `Outer.localFn`. Count an inline lambda toward its parent unit.

**Switch expressions (C# 8+, Rust match, Python match)**: same as switch statements — cyclomatic +1 per arm/pattern (except default/`_`), cognitive +1 for the expression. Pattern guards (`when`, `if` in an arm) add +1 to both.

**Comprehensions (Python) / LINQ / streams**: the construct itself is 0 for both. Conditions inside (`if` filter clause, `.Where(x => x > 0 && x < 10)`) count their `if`s and boolean operators normally.

**Exception handling**: each `catch`/`except` clause +1 both metrics. `try` and `finally` are free. A bare `except:` still counts +1.

**Recursion**: cognitive +1 for a direct recursive call (the reader must simulate the stack); cyclomatic 0.

**Async/await, yield**: 0 for both. They alter execution but not decision structure.

**Properties/getters with logic**: score a property or getter as a unit if it has a branch. Skip a pure field accessor from the per-unit sections. Keep the accessor's row in the summary table.

## Thresholds and rationale

| Range | Cyclomatic | Cognitive |
|-------|-----------|-----------|
| Fine | 1–10 | 0–15 |
| Refactor candidate | 11–20 | 16–30 |
| High risk | 21+ | 31+ |

Cyclomatic thresholds trace to McCabe's original 10-per-function guidance (testing burden: each point ≈ one test case minimum). Cognitive 15 is SonarSource's default rule threshold. Treat thresholds as alarms, not objectives. The report must point at units where a reader struggles. The report must also show that guard clauses, extraction, and flattened nesting cut real cognitive load, not just the numeric score.
