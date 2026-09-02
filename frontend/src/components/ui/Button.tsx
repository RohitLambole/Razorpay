import React from 'react'

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {variant?: 'primary'|'ghost'}

export default function Button({variant='primary', className='', children, ...rest}: Props){
  const base = 'px-4 py-2 rounded-md font-medium focus:outline-none'
  const style = variant === 'primary' ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-transparent text-indigo-700 border border-indigo-100'
  return (
    <button className={`${base} ${style} ${className}`} {...rest}>
      {children}
    </button>
  )
}
