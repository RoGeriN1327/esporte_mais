import { TbArrowLeft } from 'react-icons/tb'
import { Link } from 'react-router-dom'

// Layout das telas de acesso (login, cadastro, recuperação e redefinição de senha):
// painel da marca à esquerda no desktop e o formulário à direita; no celular, só o formulário.
export default function CartaoAuth({ titulo, subtitulo, voltarPara, voltarTexto = 'Voltar', children }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-marca-700 p-12 text-white lg:flex">
        <img
          src="/marca/padrao-quadra.svg"
          alt=""
          aria-hidden="true"
          width="600"
          height="900"
          className="pointer-events-none absolute -right-40 top-1/2 h-[120%] w-auto -translate-y-1/2 opacity-[0.09]"
        />
        <Link to="/sobre" className="relative self-start rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white">
          <img src="/marca/logo-branco.svg" alt="Esporte+ — página inicial" width="172" height="44" className="h-11 w-auto" />
        </Link>
        <div className="relative max-w-md">
          <p className="text-[2rem] font-extrabold leading-tight">
            As quadras esportivas públicas de Rio Verde, agendadas pela internet.
          </p>
          <p className="mt-4 text-lg text-marca-100">
            Consulte os horários disponíveis, faça sua reserva e acompanhe seus agendamentos sem precisar ir até a
            Secretaria.
          </p>
        </div>
        <div className="relative flex flex-wrap items-center justify-between gap-3 text-sm font-medium text-marca-200">
          <p>Secretaria Municipal de Esportes · Rio Verde – GO</p>
          <Link
            to="/sobre"
            className="rounded-md font-bold text-white underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            Regras de uso e dúvidas
          </Link>
        </div>
      </aside>

      <main className="flex flex-col px-5 py-8 sm:px-10">
        <img src="/marca/logo.svg" alt="Esporte+" width="141" height="36" className="h-9 w-auto self-start lg:hidden" />
        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-sm">
            {voltarPara && (
              <Link
                to={voltarPara}
                className="-ml-2 mb-4 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-sm font-bold text-cinza-600 transition-colors hover:bg-cinza-100 hover:text-cinza-900 focus-visible:outline-2 focus-visible:outline-marca-600"
              >
                <TbArrowLeft aria-hidden="true" className="size-4" />
                {voltarTexto}
              </Link>
            )}
            <h1 className="text-[1.75rem] font-extrabold leading-tight text-cinza-900">{titulo}</h1>
            {subtitulo && <p className="mt-2 text-cinza-600">{subtitulo}</p>}
            <div className="mt-8">{children}</div>
          </div>
        </div>
        <div className="space-y-2 text-center text-xs text-cinza-500 lg:hidden">
          <Link
            to="/sobre"
            className="rounded-md text-sm font-bold text-marca-700 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-marca-600"
          >
            Regras de uso e dúvidas
          </Link>
          <p>Secretaria Municipal de Esportes · Rio Verde – GO</p>
        </div>
      </main>
    </div>
  )
}
