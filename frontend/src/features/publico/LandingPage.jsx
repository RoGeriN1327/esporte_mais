// Página pública do Esporte+: apresentação, como funciona, regras de agendamento (com os
// valores atuais configurados pela Secretaria), conservação do patrimônio e dúvidas
// frequentes. É a página inicial de quem não está logado e fica sempre em /sobre.
import { useQuery } from '@tanstack/react-query'
import {
  TbBellRinging,
  TbCalendarCheck,
  TbCalendarRepeat,
  TbChevronDown,
  TbClockHour4,
  TbHourglass,
  TbMapPinCheck,
  TbShieldCheck,
  TbUserPlus,
} from 'react-icons/tb'
import { Link } from 'react-router-dom'

import * as regrasApi from '../../api/regras.api'
import { Alerta } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'

const CLASSE_FOCO = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600'
const BOTAO_BASE = `inline-flex h-11 items-center justify-center rounded-lg px-4 text-sm font-bold transition-colors ${CLASSE_FOCO}`

function horas(valor) {
  return `${valor} ${valor === 1 ? 'hora' : 'horas'}`
}

function duracao(minutos) {
  if (minutos % 60 === 0) return horas(minutos / 60)
  return `${minutos} minutos`
}

/** Textos das regras; sem os valores da API (erro), usa frases sem números. */
function textosDasRegras(regras) {
  const ativos = regras?.agendamentos_ativos_por_usuario
  const cancelamento = regras?.cancelamento_antecedencia_minima_horas
  const lembrete = regras?.lembrete_antecedencia_horas
  return [
    {
      Icone: TbCalendarCheck,
      titulo: ativos === undefined ? 'Um agendamento por vez' : `${ativos} agendamento por vez`,
      texto:
        'Cada cidadão pode ter apenas um agendamento confirmado ao mesmo tempo. Depois que ele acontecer, ou se você cancelar, já pode agendar de novo.',
    },
    {
      Icone: TbClockHour4,
      titulo: regras ? `Horários de ${duracao(regras.duracao_horario_minutos)}` : 'Horários de duração fixa',
      texto: 'Cada agendamento reserva a quadra por um horário. Chegue no início e libere a quadra no fim do seu horário.',
    },
    {
      Icone: TbHourglass,
      titulo:
        cancelamento === undefined
          ? 'Cancelamento com antecedência'
          : cancelamento === 0
            ? 'Cancelamento até o início'
            : `Cancelamento até ${horas(cancelamento)} antes`,
      texto:
        cancelamento === 0
          ? 'Você pode cancelar em "Meus agendamentos" até o horário começar. Assim a quadra fica livre para outra pessoa.'
          : 'Cancele em "Meus agendamentos" dentro do prazo, para a quadra ficar livre para outra pessoa. Depois do prazo, só a Secretaria pode cancelar.',
    },
    {
      Icone: TbBellRinging,
      titulo: lembrete === undefined ? 'Lembrete por e-mail' : `Lembrete ${horas(lembrete)} antes`,
      texto: 'Você recebe por e-mail a confirmação do agendamento e um lembrete antes do horário marcado.',
    },
    {
      Icone: TbCalendarRepeat,
      titulo: 'Renovação',
      texto: 'Gostou da quadra? Depois que o agendamento for concluído, você pode renová-lo para uma nova data e horário.',
    },
    {
      Icone: TbShieldCheck,
      titulo: 'Mudanças pela Secretaria',
      texto:
        'Em caso de manutenção ou evento, a Secretaria pode remarcar ou cancelar um agendamento. Você é avisado por e-mail.',
    },
  ]
}

const CONSERVACAO = [
  'Respeite o horário: chegue no início e libere a quadra no fim do seu agendamento.',
  'Use calçado e equipamentos adequados ao piso e ao esporte da quadra.',
  'Jogue o lixo nas lixeiras e deixe o espaço limpo para o próximo grupo.',
  'Não leve vidros nem objetos cortantes, e não faça fogo nas instalações.',
  'Cuide de redes, traves, alambrados e iluminação: eles são de todos.',
  'Encontrou algum dano? Comunique à Secretaria Municipal de Esportes.',
]

function perguntasFrequentes(regras) {
  const prazo = regras ? horas(regras.cancelamento_antecedencia_minima_horas) : 'o prazo definido pela Secretaria'
  return [
    {
      pergunta: 'Preciso pagar para agendar?',
      resposta: 'Não. O Esporte+ não cobra nada para consultar quadras ou fazer agendamentos.',
    },
    {
      pergunta: 'Quem pode usar o Esporte+?',
      resposta: 'Qualquer cidadão com CPF e e-mail. Basta criar uma conta, que é ativada na hora.',
    },
    {
      pergunta: 'Posso agendar mais de um horário?',
      resposta: 'Não ao mesmo tempo. Cada cidadão tem um agendamento confirmado por vez, para que mais pessoas consigam usar as quadras.',
    },
    {
      pergunta: 'Como cancelo um agendamento?',
      resposta: `Em "Meus agendamentos", escolha o agendamento e clique em "Cancelar". O cancelamento pelo sistema vale até ${prazo} antes do horário.`,
    },
    {
      pergunta: 'Perdi o prazo de cancelamento. E agora?',
      resposta: 'Procure a Secretaria Municipal de Esportes: a administração pode cancelar ou remarcar a qualquer momento.',
    },
    {
      pergunta: 'Esqueci minha senha.',
      resposta: 'Na tela de login, clique em "Esqueci minha senha" e informe seu e-mail e CPF. Você recebe um link válido por 1 hora para criar uma nova senha.',
    },
    {
      pergunta: 'Minha conta foi bloqueada. O que aconteceu?',
      resposta: 'Depois de 3 senhas erradas seguidas, a conta fica bloqueada por 1 hora, para proteger seus dados. Depois disso, é só entrar de novo.',
    },
    {
      pergunta: 'Por que fui desconectado?',
      resposta: 'Por segurança, cada acesso dura no máximo 2 horas. Se você esquecer o computador logado, ninguém consegue usar sua conta depois desse tempo.',
    },
  ]
}

function Cabecalho({ logado, destino }) {
  return (
    <header className="sticky top-0 z-30 border-b border-cinza-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6">
        <Link to="/sobre" className={`shrink-0 rounded-md ${CLASSE_FOCO} focus-visible:outline-offset-4`}>
          <img src="/marca/logo.svg" alt="Esporte+ — página inicial" width="133" height="34" className="h-[34px] w-auto" />
        </Link>
        <nav aria-label="Seções da página" className="hidden flex-1 gap-1 md:flex">
          {[
            ['#como-funciona', 'Como funciona'],
            ['#regras', 'Regras de uso'],
            ['#duvidas', 'Dúvidas frequentes'],
          ].map(([href, texto]) => (
            <a
              key={href}
              href={href}
              className={`rounded-lg px-3 py-2 text-sm font-semibold text-cinza-700 transition-colors hover:bg-cinza-100 hover:text-cinza-900 ${CLASSE_FOCO}`}
            >
              {texto}
            </a>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {logado ? (
            <Link to={destino} className={`${BOTAO_BASE} bg-marca-600 text-white hover:bg-marca-700`}>
              Ir para o sistema
            </Link>
          ) : (
            <>
              <Link to="/login" className={`${BOTAO_BASE} text-marca-700 hover:bg-marca-50`}>
                Entrar
              </Link>
              <Link to="/cadastro" className={`${BOTAO_BASE} hidden bg-marca-600 text-white hover:bg-marca-700 sm:inline-flex`}>
                Criar conta
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

function Apresentacao({ logado, destino }) {
  return (
    <section aria-labelledby="titulo-apresentacao" className="relative overflow-hidden bg-marca-700 text-white">
      <img
        src="/marca/padrao-quadra.svg"
        alt=""
        aria-hidden="true"
        width="600"
        height="900"
        className="pointer-events-none absolute -right-24 top-1/2 h-[140%] w-auto -translate-y-1/2 opacity-[0.09]"
      />
      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
        <p className="text-sm font-bold uppercase tracking-wider text-marca-200">Secretaria Municipal de Esportes · Rio Verde – GO</p>
        <h1 id="titulo-apresentacao" className="mt-4 max-w-2xl text-[2.25rem] font-black leading-tight sm:text-5xl">
          As quadras esportivas públicas de Rio Verde, agendadas pela internet.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-marca-100">
          Consulte os horários disponíveis, faça sua reserva e acompanhe seus agendamentos sem precisar ir até a Secretaria.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          {logado ? (
            <Link to={destino} className={`${BOTAO_BASE} h-12 bg-white px-6 text-marca-800 hover:bg-marca-50`}>
              Ir para o sistema
            </Link>
          ) : (
            <>
              <Link to="/cadastro" className={`${BOTAO_BASE} h-12 bg-white px-6 text-marca-800 hover:bg-marca-50`}>
                Criar minha conta
              </Link>
              <Link to="/login" className={`${BOTAO_BASE} h-12 border border-white/40 px-6 text-white hover:bg-white/10`}>
                Já tenho conta
              </Link>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

function Secao({ id, titulo, descricao, children, fundo = 'bg-cinza-50' }) {
  return (
    <section id={id} aria-labelledby={`titulo-${id}`} className={`scroll-mt-16 ${fundo}`}>
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <h2 id={`titulo-${id}`} className="text-[1.75rem] font-black leading-tight text-cinza-900">
          {titulo}
        </h2>
        {descricao && <p className="mt-2 max-w-2xl text-cinza-600">{descricao}</p>}
        <div className="mt-8">{children}</div>
      </div>
    </section>
  )
}

const PASSOS = [
  { Icone: TbUserPlus, titulo: 'Crie sua conta', texto: 'Cadastre-se com nome, CPF e e-mail. A conta fica ativa na hora.' },
  { Icone: TbCalendarCheck, titulo: 'Escolha quadra e horário', texto: 'Veja as quadras por esporte e bairro e escolha um horário livre.' },
  { Icone: TbMapPinCheck, titulo: 'Compareça e jogue', texto: 'Você recebe a confirmação por e-mail e um lembrete antes do horário.' },
]

export default function LandingPage() {
  const { usuario } = useAuth()
  const logado = Boolean(usuario)
  const destino = usuario?.tipo === 'Administrativo' ? '/admin' : '/'
  const { data: regras, isLoading, isError } = useQuery({
    queryKey: ['regras-de-uso'],
    queryFn: regrasApi.obterRegras,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <div className="min-h-dvh bg-cinza-50">
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:font-bold focus:text-marca-700 focus:shadow"
      >
        Pular para o conteúdo
      </a>
      <Cabecalho logado={logado} destino={destino} />

      <main id="conteudo">
        <Apresentacao logado={logado} destino={destino} />

        <Secao id="como-funciona" titulo="Como funciona" descricao="Agendar uma quadra pública leva poucos minutos.">
          <ol className="grid gap-4 sm:grid-cols-3">
            {PASSOS.map(({ Icone, titulo, texto }, indice) => (
              <li key={titulo} className="rounded-2xl border border-cinza-200 bg-white p-6">
                <div className="flex items-center gap-3">
                  <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
                    <Icone aria-hidden="true" className="size-6" />
                  </span>
                  <span className="text-sm font-bold text-marca-700">Passo {indice + 1}</span>
                </div>
                <h3 className="mt-4 text-lg font-extrabold text-cinza-900">{titulo}</h3>
                <p className="mt-1.5 text-sm text-cinza-600">{texto}</p>
              </li>
            ))}
          </ol>
        </Secao>

        <Secao
          id="regras"
          fundo="bg-white"
          titulo="Regras de agendamento"
          descricao="Valem para todas as quadras e garantem que mais pessoas consigam usar os espaços públicos."
        >
          {isError && (
            <div className="mb-6">
              <Alerta tipo="aviso">Não foi possível carregar os prazos atuais. Confira-os no sistema ou com a Secretaria.</Alerta>
            </div>
          )}
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy={isLoading || undefined}>
            {textosDasRegras(isLoading ? undefined : regras).map(({ Icone, titulo, texto }) => (
              <li key={texto} className="flex gap-4 rounded-2xl border border-cinza-200 bg-cinza-50 p-5">
                <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-marca-50 text-marca-700">
                  <Icone aria-hidden="true" className="size-6" />
                </span>
                <div>
                  <h3 className="font-extrabold text-cinza-900">{titulo}</h3>
                  <p className="mt-1 text-sm text-cinza-600">{texto}</p>
                </div>
              </li>
            ))}
          </ul>
        </Secao>

        <Secao
          id="conservacao"
          titulo="Cuide do que é de todos"
          descricao="As quadras são patrimônio público. Algumas orientações para que continuem em bom estado:"
        >
          <ul className="grid gap-3 sm:grid-cols-2">
            {CONSERVACAO.map((item) => (
              <li key={item} className="flex items-start gap-3 rounded-xl bg-white p-4 text-cinza-700 ring-1 ring-cinza-200">
                <TbShieldCheck aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-marca-600" />
                {item}
              </li>
            ))}
          </ul>
        </Secao>

        <Secao id="duvidas" fundo="bg-white" titulo="Dúvidas frequentes">
          <div className="divide-y divide-cinza-200 rounded-2xl border border-cinza-200">
            {perguntasFrequentes(isLoading ? undefined : regras).map(({ pergunta, resposta }) => (
              <details key={pergunta} className="group">
                <summary
                  className={`flex cursor-pointer list-none items-center justify-between gap-4 rounded-2xl px-5 py-4 font-bold text-cinza-900 hover:bg-cinza-50 [&::-webkit-details-marker]:hidden ${CLASSE_FOCO} focus-visible:-outline-offset-2`}
                >
                  {pergunta}
                  <TbChevronDown aria-hidden="true" className="size-5 shrink-0 text-cinza-500 transition-transform group-open:rotate-180" />
                </summary>
                <p className="px-5 pb-5 text-cinza-600">{resposta}</p>
              </details>
            ))}
          </div>
        </Secao>
      </main>

      <footer className="bg-marca-800 text-marca-100">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-10 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <img src="/marca/logo-branco.svg" alt="Esporte+" width="141" height="36" className="h-9 w-auto self-start" />
          <p className="text-sm">Secretaria Municipal de Esportes · Rio Verde – GO</p>
        </div>
      </footer>
    </div>
  )
}
