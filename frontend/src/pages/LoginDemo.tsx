import React, {useState} from 'react'
import { useNavigate } from 'react-router-dom'
import { useDemoAuth } from '../hooks/useDemoAuth'

export default function LoginDemo(){
  const navigate = useNavigate()
  const { signInDemo } = useDemoAuth()
  const [name, setName] = useState('Demo User')

  function submit(e: React.FormEvent){
    e.preventDefault()
    signInDemo(name)
    navigate('/app')
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold">Demo Login</h2>
        <p className="mt-2 text-sm text-gray-600">Sign in to a demo merchant account for showcasing Agentic Commerce.</p>
        <form className="mt-6" onSubmit={submit}>
          <label className="block text-sm font-medium">Your name</label>
          <input value={name} onChange={(e)=>setName(e.target.value)} className="mt-2 w-full border rounded px-3 py-2" />
          <div className="mt-6 flex justify-end">
            <button className="px-4 py-2 bg-indigo-600 text-white rounded">Enter demo</button>
          </div>
        </form>
      </div>
    </div>
  )
}
