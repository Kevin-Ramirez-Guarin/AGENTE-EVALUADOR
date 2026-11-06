import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { ComoEvaluamos } from './pages/ComoEvaluamos'
import { Detalle } from './pages/Detalle'
import { Aplicar } from './pages/Aplicar'
import { Panel } from './pages/Panel'
import { Privacidad } from './pages/Privacidad'
import { Vacantes } from './pages/Vacantes'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a href="#contenido" className="sr-only focus:not-sr-only focus:absolute focus:bg-white focus:p-2">Saltar al contenido</a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <Link to="/vacantes" className="text-xl font-bold text-indigo-800 focus-visible:outline-2 focus-visible:outline-indigo-700">Nexo Digital</Link>
          <nav aria-label="Principal" className="flex gap-4 font-medium">
            <Link to="/vacantes" className="text-indigo-800 underline focus-visible:outline-2 focus-visible:outline-indigo-700">Vacantes</Link>
            <Link to="/panel" className="text-indigo-800 underline focus-visible:outline-2 focus-visible:outline-indigo-700">Panel</Link>
          </nav>
        </div>
      </header>
      <main id="contenido" className="mx-auto max-w-5xl px-4 py-8">
        <Routes>
          <Route path="/vacantes" element={<Vacantes />} />
          <Route path="/aplicar/:id" element={<Aplicar />} />
          <Route path="/panel" element={<Panel />} />
          <Route path="/panel/:id" element={<Detalle />} />
          <Route path="/privacidad" element={<Privacidad />} />
          <Route path="/como-evaluamos" element={<ComoEvaluamos />} />
          <Route path="*" element={<Navigate to="/vacantes" replace />} />
        </Routes>
      </main>
    </div>
  )
}
