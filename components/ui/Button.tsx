import React from 'react'
import { motion } from 'framer-motion'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  onClick?: () => void
  className?: string
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  onClick,
  className = ''
}) => {
  const baseClasses = 'font-semibold rounded-lg transition-all duration-200 cursor-pointer inline-block text-center border'
  
  const variantClasses = {
    primary: 'bg-primary-600 hover:bg-primary-700 text-white border-primary-600 hover:border-primary-700 shadow-lg hover:shadow-primary-600/25',
    secondary: 'border-primary-600 hover:bg-primary-600 hover:text-white text-primary-600 bg-transparent',
    ghost: 'border-gray-600 hover:bg-gray-800 hover:text-white text-gray-300 bg-transparent'
  }
  
  const sizeClasses = {
    sm: 'py-2 px-4 text-sm',
    md: 'py-3 px-6 text-base',
    lg: 'py-4 px-8 text-lg'
  }
  
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      onClick={onClick}
    >
      {children}
    </motion.button>
  )
}