// Polyfill for Chromium < 126 (Electron 30)
if (typeof URL !== 'undefined' && !URL.parse) {
  URL.parse = (url, base) => {
    try { return new URL(url, base); } catch { return null; }
  };
}

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
