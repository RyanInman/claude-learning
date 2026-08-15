import csv


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def total_by_region(path):
    totals = {}
    for row in load(path):
        region = row["region"]
        totals[region] = totals.get(region, 0.0) + float(row["amount"])
    return totals


if __name__ == "__main__":
    import sys

    for region, amount in sorted(total_by_region(sys.argv[1]).items()):
        print(f"{region}\t{amount:.2f}")
