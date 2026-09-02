import React from 'react'

export default function Input(props: React.InputHTMLAttributes<HTMLInputElement>){
  return <input className="w-full border rounded px-3 py-2" {...props} />
}
