import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { Aplicar } from './pages/Aplicar'
import { Privacidad } from './pages/Privacidad'
import { Vacantes } from './pages/Vacantes'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a href="#contenido" className="sr-only focus:not-sr-only focus:absolute focus:bg-white focus:p-2">Saltar al contenido</a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <Link to="/vacantes" className="text-xl font-bold text-indigo-800 focus-visible:outline-2 focus-visible:outline-indigo-700">Nexo Digital</Link>
        </div>
      </header>
      <main id="contenido" className="mx-auto max-w-3xl px-4 py-8">
        <Routes>
          <Route path="/vacantes" element={<Vacantes />} />
          <Route path="/aplicar/:id" element={<Aplicar />} />
          <Route path="/privacidad" element={<Privacidad />} />
          <Route path="*" element={<Navigate to="/vacantes" replace />} />
        </Routes>
      </main>
    </div>
  )
}
