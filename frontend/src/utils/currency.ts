export function formatINR(cents: number){
  return (cents/100).toLocaleString('en-IN', {style:'currency', currency:'INR'})
}
