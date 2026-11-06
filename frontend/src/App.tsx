import { useEffect } from 'react'
import { Link, Navigate, NavLink, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { Aplicar } from './pages/Aplicar'
import { ComoEvaluamos } from './pages/ComoEvaluamos'
import { Detalle } from './pages/Detalle'
import { Panel } from './pages/Panel'
import { Privacidad } from './pages/Privacidad'
import { Vacantes } from './pages/Vacantes'
import { Logo, Marca } from './ui'

const SaltarAlContenido = () => (
  <a
    href="#contenido"
    className="sr-only z-50 rounded-md bg-white px-4 py-2 font-semibold text-selva-900 shadow-elevada focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
  >
    Saltar al contenido
  </a>
)

const Contenido = ({ className = '' }: { className?: string }) => (
  <main id="contenido" tabIndex={-1} className={`focus-visible:outline-none ${className}`}>
    <Outlet />
  </main>
)

const navClase =
  'rounded-full px-3 py-2 font-medium text-caribe-100 transition-colors duration-150 hover:bg-white/10 hover:text-white aria-[current=page]:bg-white/12 aria-[current=page]:text-white'

// Sitio público de empleo: expresivo, con la marca al frente.
function SitioEmpleo() {
  return (
    <div className="flex min-h-screen flex-col">
      <SaltarAlContenido />
      <header data-tono="oscuro" className="bg-selva-900">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-1 px-4 py-4 sm:px-6">
          <Link to="/vacantes" aria-label="Giveaway, empleos" className="rounded-md">
            <Logo />
          </Link>
          <nav aria-label="Principal" className="-mr-3">
            <ul className="flex text-[0.9375rem] sm:text-base">
              <li><NavLink to="/vacantes" className={navClase}>Vacantes</NavLink></li>
              <li><NavLink to="/como-evaluamos" className={navClase}>Cómo evaluamos</NavLink></li>
            </ul>
          </nav>
        </div>
      </header>
      <Contenido className="flex-1" />
      <footer data-tono="oscuro" className="bg-selva-950 text-caribe-100">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:grid-cols-[1fr_auto] sm:px-6">
          <div className="max-w-sm space-y-3">
            <Logo />
            <p className="text-sm leading-relaxed">
              Giveaway S.A.S., Medellín, Colombia. Tours y experiencias con guías locales certificados en Cartagena,
              Medellín, el Eje Cafetero, el Parque Tayrona, Bogotá y Guatapé.
            </p>
          </div>
          <nav aria-label="Pie de página">
            <ul className="space-y-1 text-sm">
              <li><Link to="/vacantes" className="inline-block py-1 underline-offset-4 hover:text-white hover:underline">Vacantes</Link></li>
              <li><Link to="/privacidad" className="inline-block py-1 underline-offset-4 hover:text-white hover:underline">Política de privacidad</Link></li>
              <li><Link to="/panel" className="inline-block py-1 underline-offset-4 hover:text-white hover:underline">Panel de Talento</Link></li>
            </ul>
          </nav>
        </div>
      </footer>
    </div>
  )
}

// Herramienta interna: sobria y densa, con fondo neutro para no confundirse con el sitio público.
function PanelTalento() {
  return (
    <div className="min-h-screen bg-niebla-100">
      <SaltarAlContenido />
      <header data-tono="oscuro" className="bg-selva-950">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-2.5 sm:px-6">
          <Link to="/panel" className="flex items-center gap-2.5 rounded-md text-white">
            <Marca className="h-7 w-auto" />
            <span className="font-display text-lg font-bold tracking-[-0.03em]">giveaway</span>
            <span aria-hidden="true" className="h-5 w-px bg-white/25" />
            <span className="font-medium text-caribe-100">Talento</span>
          </Link>
          <Link to="/vacantes" className="rounded-full px-3 py-1.5 text-sm font-medium text-caribe-100 hover:bg-white/10 hover:text-white">
            Ver sitio de empleo
          </Link>
        </div>
      </header>
      <Contenido className="mx-auto max-w-7xl px-4 py-8 sm:px-6" />
    </div>
  )
}

export default function App() {
  const { pathname } = useLocation()
  // BrowserRouter no restaura el scroll: cada página nueva arranca arriba.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <Routes>
      <Route element={<SitioEmpleo />}>
        <Route path="/vacantes" element={<Vacantes />} />
        <Route path="/aplicar/:id" element={<Aplicar />} />
        <Route path="/privacidad" element={<Privacidad />} />
        <Route path="/como-evaluamos" element={<ComoEvaluamos />} />
      </Route>
      <Route element={<PanelTalento />}>
        <Route path="/panel" element={<Panel />} />
        <Route path="/panel/:id" element={<Detalle />} />
      </Route>
      <Route path="*" element={<Navigate to="/vacantes" replace />} />
    </Routes>
  )
}
