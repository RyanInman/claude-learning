export function average(xs: number[]) {
  var total = 0;
  for (const x of xs) total += x;
  console.log("computed average over", xs.length, "items");
  return total / xs.length;
}
