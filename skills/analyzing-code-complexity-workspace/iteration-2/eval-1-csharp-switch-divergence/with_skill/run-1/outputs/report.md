# Complexity Report: PaymentService.cs

## Summary

| Unit | Cyclomatic | Cognitive | Assessment |
|------|-----------|-----------|------------|
| PaymentService.Process | 6 | 12 | ✅ |
| PaymentService.StatusLabel | 6 | 1 | ✅ |
| PaymentService.Charge | 3 | 2 | ✅ |
| PaymentService.Discount | 3 | 2 | ✅ |
| PaymentService.Retry | 1 | 0 | ✅ |
| PaymentService.Log | 1 | 0 | ✅ |
| PaymentService.Ship | 1 | 0 | ✅ |
| PaymentService.Notify | 1 | 0 | ✅ |

## PaymentService.Process

**Cyclomatic: 6** — base 1 + 2 foreach + 2 if + 1 `||`
**Cognitive: 12** — 2 foreach + 2 if + 1 `||` + 1 else + nesting penalties (+1, +2, +3)

```csharp
public void Process(List<Order> orders)
{
    foreach (var o in orders)                    // CC +1 | Cog +1
    {
        if (o.Paid)                              // CC +1 | Cog +1, nesting +1
        {
            foreach (var i in o.Items)           // CC +1 | Cog +1, nesting +2
            {
                if (i.InStock || i.Backorderable)// CC +1, || +1 | Cog +1, nesting +3, || +1
                {
                    Ship(i);
                }
                else                             // CC 0 | Cog +1
                {
                    Notify(o, i);
                }
            }
        }
    }
}
```

Highest cognitive score in the file, and the widest divergence in the other direction from StatusLabel: only 6 paths to test, but 4 nested structures mean nesting penalties (+1, +2, +3) contribute half the cognitive score. The reader must hold loop-within-condition-within-loop context to follow any single line. Extracting the inner loop removes the deep nesting without changing behavior:

```csharp
public void Process(List<Order> orders)
{
    foreach (var o in orders)                        // CC +1 | Cog +1
        if (o.Paid) ShipItems(o);                    // CC +1 | Cog +1, nesting +1
}
private void ShipItems(Order o)
{
    foreach (var i in o.Items)                       // CC +1 | Cog +1
        if (i.InStock || i.Backorderable) Ship(i);   // CC +1, || +1 | Cog +1, nesting +1, || +1
        else Notify(o, i);                           // Cog +1
}
// Process: cyclomatic 3, cognitive 3   ShipItems: cyclomatic 4, cognitive 5
```

Same total paths, cognitive drops from 12 in one unit to 3 + 5 across two.

## PaymentService.Charge

**Cyclomatic: 3** — base 1 + 2 catch
**Cognitive: 2** — 2 catch, no nesting penalties (try is free, catches are top-level)

```csharp
public decimal Charge(Order o)
{
    try
    {
        return gateway.Charge(o.Total);
    }
    catch (TimeoutException)      // CC +1 | Cog +1
    {
        return Retry(o);
    }
    catch (GatewayException e)    // CC +1 | Cog +1
    {
        Log(e);
        throw;
    }
}
```

Two catch clauses give two extra paths and two flow-breaks; `try` and the rethrow cost nothing. Handlers are flat and single-purpose, so scores stay low and aligned. No action needed.

## PaymentService.Discount

**Cyclomatic: 3** — base 1 + 1 ternary + 1 `&&`
**Cognitive: 2** — 1 ternary + 1 `&&`

```csharp
public decimal Discount(Customer c)
{
    return c.IsVip && c.Years > 5 ? 0.2m : 0.05m;  // CC +1 &&, +1 ?: | Cog +1 &&, +1 ?:
}
```

One compound condition feeding one ternary: three test paths (VIP long-tenure, VIP short-tenure via `&&` short-circuit, non-VIP), trivial reading cost. Fine as is.

## PaymentService.StatusLabel

**Cyclomatic: 6** — base 1 + 5 case (default is free)
**Cognitive: 1** — the switch itself; individual cases cost nothing

```csharp
public string StatusLabel(int code)
{
    switch (code)              // CC 0 | Cog +1
    {
        case 0: return "pending";    // CC +1
        case 1: return "paid";       // CC +1
        case 2: return "shipped";    // CC +1
        case 3: return "delivered";  // CC +1
        case 4: return "returned";   // CC +1
        default: return "unknown";   // CC 0
    }
}
```

The file's clearest metric divergence: cyclomatic ties Process at 6 while cognitive is 1. Cyclomatic charges per case because each is an independent path needing a test; cognitive charges once because a flat value-mapping switch reads top to bottom with no state to track. Many test paths, low reading cost — not a refactor candidate.

---

Trivial units (Retry, Log, Ship, Notify) score 1/0 — no branching, no explanation needed.

*Convention note: `&&`/`||` counted per operator for both metrics; SonarQube's cognitive spec counts a run of like operators as +1 total, so its cognitive numbers may read slightly lower.*
