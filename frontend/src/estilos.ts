// Clases de botón: sirven tanto para <button> como para <Link>.
const BASE_BOTON =
  'inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-[background-color,box-shadow,transform] duration-150 ease-out active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100'
const VARIANTES = {
  primario: 'bg-caribe-700 text-white shadow-tarjeta hover:bg-caribe-800',
  acento: 'bg-mango-400 text-selva-950 hover:bg-mango-300',
  secundario: 'bg-white text-niebla-900 ring-1 ring-inset ring-niebla-300 hover:bg-niebla-100',
  peligro: 'bg-red-700 text-white hover:bg-red-800',
}
const TAMANOS = { normal: 'min-h-11 px-5', compacto: 'min-h-9 px-3.5 text-sm' }

export const boton = (variante: keyof typeof VARIANTES = 'primario', tamano: keyof typeof TAMANOS = 'normal') =>
  `${BASE_BOTON} ${VARIANTES[variante]} ${TAMANOS[tamano]}`

export const enlace = 'font-medium text-caribe-800 underline decoration-caribe-500/50 underline-offset-[3px] hover:decoration-caribe-800'

export const campoClase =
  'mt-1.5 block w-full rounded-md border border-niebla-500 bg-white px-3.5 py-2.5 text-niebla-900 transition-[border-color,box-shadow] duration-150 hover:border-niebla-700 aria-[invalid=true]:border-red-700 aria-[invalid=true]:ring-1 aria-[invalid=true]:ring-red-700 disabled:border-niebla-300 disabled:bg-niebla-100 disabled:text-niebla-600'
