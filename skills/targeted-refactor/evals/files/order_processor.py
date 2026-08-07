def calc_shipping(o, u):
    if o is not None:
        if len(o["items"]) > 0:
            if u["country"] == "US":
                if o["weight"] > 50:
                    if u["is_member"]:
                        cost = 15
                    else:
                        cost = 25
                else:
                    if u["is_member"]:
                        cost = 5
                    else:
                        cost = 10
            else:
                if o["weight"] > 50:
                    if u["is_member"]:
                        cost = 40
                    else:
                        cost = 60
                else:
                    if u["is_member"]:
                        cost = 20
                    else:
                        cost = 35
        else:
            cost = 0
    else:
        cost = 0
    return cost
