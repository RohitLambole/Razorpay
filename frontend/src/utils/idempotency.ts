export function generateIdempotencyKey(quoteId?: string){
  const ts = Date.now().toString(36)
  const rand = Math.random().toString(36).slice(2,9)
  return `${quoteId?quoteId+'-':''}${ts}-${rand}`
}
