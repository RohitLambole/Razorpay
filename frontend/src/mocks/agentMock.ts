// isolated mock adapter for agent flows (clearly labeled)
export async function mockAgentSuggest(intent: string, catalog: any[]){
  // naive match: find product whose name includes a keyword
  const lower = intent.toLowerCase()
  const found = catalog.find((p:any)=> (p.name || '').toLowerCase().includes(lower.split(' ')[0])) || catalog[0]
  return {
    product: found,
    suggested_quantity: 1,
    suggested_discount_percent: 10,
    note: 'This is a demo suggestion. Replace with server-side LLM when available.'
  }
}
