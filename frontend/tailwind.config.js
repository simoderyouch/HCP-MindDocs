const colors = require('tailwindcss/colors')

/** @type {import('tailwindcss').Config} */
module.exports = {

    content: [
      './src/**/*.{js,jsx,ts,tsx}',
      './node_modules/flowbite/**/*.js'
    ],
    theme: {
      borderRadius: {
        'none': '0',
        'sm': '0.125rem',
        'sm2' : '0.2rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'full': '9999px',
        'large': '12px',
      },
      screens: {
        'sm': '640px',
        'md': '768px',
        'lg': '1020px',
        'xl': '1280px',
      },
      fontSize: {
        xs: '0.7rem',
        sm: '0.8rem',
        base: '1rem',
        xl: '1.25rem',
        '2xl': '1.563rem',
        '3xl': '1.953rem',
        '4xl': '2.441rem',
        '5xl': '3.052rem',
      },
      extend: {
        colors: {
          
          'primary': '#711037',
          
          'secondry': '#f4982f',
          'dark': '#272d37'

          
      },
      },

      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '2rem',
          lg: '4rem',
          xl: '5rem',
          '2xl': '6rem',
        },
      },
    },
    plugins: [
      require('flowbite/plugin')
  ]
  }