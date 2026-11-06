import { Link } from 'react-router-dom'
import { enlace } from '../estilos'
import { BandaTitulo } from '../ui'

export function Privacidad() {
  return (
    <>
      <BandaTitulo titulo="Política de privacidad">
        <p className="max-w-2xl text-lg leading-relaxed text-caribe-100">Qué hacemos con tus datos cuando te postulas a una vacante de Giveaway.</p>
      </BandaTitulo>
      <article className="mx-auto max-w-3xl space-y-5 px-4 py-12 leading-relaxed text-niebla-700 sm:px-6 sm:py-16">
        <p>
          Giveaway trata tus datos personales conforme a la Ley 1581 de 2012. Usamos tu nombre, correo y hoja de vida
          únicamente para evaluar tu postulación a la vacante elegida.
        </p>
        <p>
          Una herramienta de inteligencia artificial analiza tu hoja de vida y sugiere un resultado, pero la decisión final
          siempre la toma una persona del equipo de Talento.
        </p>
        <p>
          Mira con detalle <Link to="/como-evaluamos" className={enlace}>cómo evaluamos tu hoja de vida</Link>.
        </p>
        <p>
          No compartimos tus datos con terceros ni los usamos para otros fines. Puedes pedir en cualquier momento conocer,
          corregir o eliminar tu información escribiendo a{' '}
          <a href="mailto:privacidad@giveaway.example" className={enlace}>privacidad@giveaway.example</a>.
        </p>
      </article>
    </>
  )
}
