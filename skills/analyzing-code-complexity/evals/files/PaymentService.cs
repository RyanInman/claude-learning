using System;
using System.Collections.Generic;

public class PaymentService
{
    private readonly IGateway gateway;

    public string StatusLabel(int code)
    {
        switch (code)
        {
            case 0: return "pending";
            case 1: return "paid";
            case 2: return "shipped";
            case 3: return "delivered";
            case 4: return "returned";
            default: return "unknown";
        }
    }

    public decimal Charge(Order o)
    {
        try
        {
            return gateway.Charge(o.Total);
        }
        catch (TimeoutException)
        {
            return Retry(o);
        }
        catch (GatewayException e)
        {
            Log(e);
            throw;
        }
    }

    public decimal Discount(Customer c)
    {
        return c.IsVip && c.Years > 5 ? 0.2m : 0.05m;
    }

    public void Process(List<Order> orders)
    {
        foreach (var o in orders)
        {
            if (o.Paid)
            {
                foreach (var i in o.Items)
                {
                    if (i.InStock || i.Backorderable)
                    {
                        Ship(i);
                    }
                    else
                    {
                        Notify(o, i);
                    }
                }
            }
        }
    }

    private decimal Retry(Order o) => gateway.Charge(o.Total);
    private void Log(Exception e) { }
    private void Ship(Item i) { }
    private void Notify(Order o, Item i) { }
}
