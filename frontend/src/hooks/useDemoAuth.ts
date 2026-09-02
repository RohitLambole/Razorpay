import { useState } from 'react'

const DEFAULT_MERCHANT = import.meta.env.VITE_DEFAULT_MERCHANT_ID || '146cf105-7ad7-48f8-8cc6-77f958febf0d'

export function useDemoAuth(){
  const [merchantId] = useState<string>(DEFAULT_MERCHANT)
  const [userName, setUserName] = useState<string | null>(null)

  function signInDemo(name: string){
    setUserName(name)
    // persist demo session
    localStorage.setItem('demo_user', JSON.stringify({name, merchantId}))
  }

  function signOut(){
    setUserName(null)
    localStorage.removeItem('demo_user')
  }

  // hydrate
  if(!userName){
    const raw = localStorage.getItem('demo_user')
    if(raw){
      try{const obj = JSON.parse(raw); setUserName(obj.name)}catch(e){}
    }
  }

  return {userName, merchantId, signInDemo, signOut}
}
