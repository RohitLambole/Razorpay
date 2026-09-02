const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://razorpay-backend-j4mc.onrender.com'

export async function apiGet(path: string){
  const res = await fetch(`${API_BASE}${path}`)
  if(!res.ok) throw new Error(`API GET ${path} failed: ${res.status}`)
  return res.json()
}

export async function apiPost(path: string, body: any){
  const res = await fetch(`${API_BASE}${path}`,{
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })
  const text = await res.text()
  try{
    const data = text ? JSON.parse(text) : null
    if(!res.ok) throw new Error(`API POST ${path} failed: ${res.status} ${JSON.stringify(data)}`)
    return data
  }catch(e){
    throw e
  }
}
