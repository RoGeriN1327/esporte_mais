// Gerenciar administradores (RF001: A4 cadastrar, A5 editar e A6 desativar Gestor ou Operador;
// Quadros 16 a 18 do DERS). Só o Gestor acessa. A consulta carrega a lista ao clicar em "Buscar"
// e filtra por nome, perfil e status no navegador (a API devolve a lista completa).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { TbShieldSearch, TbUserPlus } from 'react-icons/tb'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import Avatar from '../../components/Avatar'
import {
  BarraAcoes,
  BotoesFiltro,
  CabecalhoPagina,
  ItemClicavel,
  ListaClicavel,
  ListaDetalhes,
  PainelFiltros,
  ResultadoConsulta,
} from '../../components/Pagina'
import { classesDeInput } from '../../components/estilos'
import { Alerta, Badge, Botao, Campo, Modal } from '../../components/ui'
import { useAuth } from '../../contexts/useAuth'
import { useConsulta } from '../../hooks/useConsulta'
import { cpfValido, mascararCpf } from '../../utils/cpf'
import { formatarData } from '../../utils/datas'
import { normalizarTexto } from '../../utils/texto'

const CHAVES = ['nome', 'perfil', 'status']

function filtrar(administradores, { nome, perfil, status }) {
  const termo = normalizarTexto(nome)
  return administradores.filter(
    (admin) =>
      (!termo || normalizarTexto(admin.nome).includes(termo)) &&
      (!perfil || admin.perfil === perfil) &&
      (!status || admin.status === status),
  )
}

function FormularioAdministrador({ inicial, aoSalvar, aoCancelar, salvando, erro }) {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm({
    defaultValues: inicial
      ? { nome: inicial.nome, cpf: mascararCpf(inicial.cpf), email: inicial.email, perfil: inicial.perfil }
      : { nome: '', cpf: '', email: '', perfil: '' },
  })

  return (
    <form className="space-y-5" onSubmit={handleSubmit(aoSalvar)} noValidate>
      <Campo label="Nome completo" erro={errors.nome?.message}>
        <input
          className={classesDeInput(errors.nome)}
          autoComplete="off"
          maxLength={100}
          {...register('nome', { required: 'Informe o nome completo.' })}
        />
      </Campo>
      <div className="grid gap-5 sm:grid-cols-2">
        <Campo label="CPF" erro={errors.cpf?.message}>
          <input
            className={`${classesDeInput(errors.cpf)} tabular-nums`}
            inputMode="numeric"
            autoComplete="off"
            placeholder="000.000.000-00"
            {...register('cpf', {
              required: 'Informe o CPF.',
              validate: (valor) => cpfValido(valor) || 'CPF inválido. Informe 11 dígitos numéricos válidos.',
              onChange: (evento) => setValue('cpf', mascararCpf(evento.target.value)),
            })}
          />
        </Campo>
        <Campo label="Perfil" erro={errors.perfil?.message}>
          <select className={classesDeInput(errors.perfil)} {...register('perfil', { required: 'Selecione o perfil.' })}>
            <option value="">Selecione…</option>
            <option value="Operador">Operador</option>
            <option value="Gestor">Gestor</option>
          </select>
        </Campo>
      </div>
      <Campo
        label="E-mail"
        erro={errors.email?.message}
        dica={inicial ? 'A alteração de perfil passa a valer na próxima sessão.' : 'A senha temporária de acesso é enviada para este e-mail.'}
      >
        <input
          type="email"
          inputMode="email"
          autoComplete="off"
          spellCheck={false}
          placeholder="nome@exemplo.com"
          className={classesDeInput(errors.email)}
          {...register('email', {
            required: 'Informe o e-mail.',
            pattern: { value: /.+@.+\..+/, message: 'Informe um e-mail válido, no formato nome@exemplo.com.' },
          })}
        />
      </Campo>
      <Alerta tipo="erro">{erro}</Alerta>
      <BarraAcoes separada>
        <Botao type="button" variante="secundario" onClick={aoCancelar}>
          Cancelar
        </Botao>
        <Botao type="submit" carregando={salvando}>
          {salvando ? 'Salvando…' : 'Salvar'}
        </Botao>
      </BarraAcoes>
    </form>
  )
}

export default function AdministradoresPage() {
  const queryClient = useQueryClient()
  const { usuario: usuarioLogado } = useAuth()
  const consulta = useConsulta(CHAVES)
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)

  const { data: todos, isFetching, isError } = useQuery({
    queryKey: ['admin-administradores'],
    queryFn: adminApi.listarAdministradores,
    enabled: consulta.consultado,
  })
  const administradores = todos ? filtrar(todos, consulta.filtros) : undefined

  function abrir(config) {
    setErroModal('')
    setModal(config)
  }

  function aoTerminar(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-administradores'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const cadastrar = useMutation({
    mutationFn: adminApi.cadastrarAdministrador,
    ...aoTerminar('Administrador cadastrado. A senha temporária foi enviada para o e-mail informado.'),
  })
  const editar = useMutation({
    mutationFn: ({ id, dados }) => adminApi.editarAdministrador(id, dados),
    ...aoTerminar('Administrador atualizado. A alteração de perfil vale a partir da próxima sessão.'),
  })
  const desativar = useMutation({
    mutationFn: (id) => adminApi.desativarAdministrador(id),
    ...aoTerminar('Administrador desativado. As sessões ativas foram encerradas.'),
  })

  const detalhe = modal?.modo === 'detalhes' ? modal.admin : null
  const ehVoce = (admin) => admin.id === usuarioLogado?.id

  return (
    <div>
      <CabecalhoPagina
        voltarPara="/admin"
        voltarTexto="Início"
        titulo="Gerenciar administradores"
        descricao="Consulte os Gestores e Operadores. Abra um administrador para ver os dados, editar ou desativar."
        acoes={
          <Botao onClick={() => abrir({ modo: 'novo' })}>
            <TbUserPlus aria-hidden="true" className="size-[18px]" />
            Cadastrar Administrador
          </Botao>
        }
      />

      <div className="space-y-8">
        <PainelFiltros
          key={consulta.versao}
          onBuscar={(dados) => consulta.buscar(Object.fromEntries(dados))}
          botoes={<BotoesFiltro onLimpar={consulta.limpar} buscando={isFetching && consulta.consultado} />}
        >
          <Campo label="Nome">
            <input name="nome" defaultValue={consulta.filtros.nome} autoComplete="off" placeholder="Nome completo ou parte…" className={classesDeInput(false)} />
          </Campo>
          <Campo label="Perfil">
            <select name="perfil" defaultValue={consulta.filtros.perfil} className={classesDeInput(false)}>
              <option value="">Todos</option>
              <option value="Gestor">Gestor</option>
              <option value="Operador">Operador</option>
            </select>
          </Campo>
          <Campo label="Status">
            <select name="status" defaultValue={consulta.filtros.status} className={classesDeInput(false)}>
              <option value="">Todos</option>
              <option value="Ativo">Ativo</option>
              <option value="Desativado">Desativado</option>
            </select>
          </Campo>
        </PainelFiltros>

        <Alerta tipo="sucesso">{mensagem}</Alerta>

        <ResultadoConsulta
          consultado={consulta.consultado}
          carregando={isFetching && !todos}
          erro={isError && 'Não foi possível buscar os administradores. Tente novamente em instantes.'}
          vazio={!administradores?.length}
          inicial={{
            Icone: TbShieldSearch,
            titulo: 'Consulte os administradores',
            descricao: 'Filtre por nome, perfil ou status e clique em “Buscar”. Para listar todos, clique em “Buscar” sem preencher nada.',
          }}
          textoCarregando="Buscando administradores…"
          tituloVazio="Nenhum administrador encontrado"
          descricaoVazio="Não há administradores com esses filtros. Altere a busca ou use “Limpar filtros” para ver todos."
        >
          <ListaClicavel titulo="Administradores" total={administradores?.length} rotuloSingular="administrador" rotuloPlural="administradores">
            {administradores?.map((admin) => (
              <ItemClicavel key={admin.id} onClick={() => abrir({ modo: 'detalhes', admin })}>
                <Avatar nome={admin.nome} tamanho="medio" apagado={admin.status !== 'Ativo'} />
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className="truncate font-extrabold text-cinza-900">{admin.nome}</span>
                    {ehVoce(admin) && <span className="shrink-0 rounded bg-cinza-100 px-1.5 py-0.5 text-[11px] font-bold text-cinza-600">Você</span>}
                  </span>
                  <span className="mt-0.5 block truncate text-sm text-cinza-600">
                    <span className="font-semibold text-marca-700">{admin.perfil}</span> · {admin.email}
                  </span>
                </span>
                <Badge>{admin.status}</Badge>
              </ItemClicavel>
            ))}
          </ListaClicavel>
        </ResultadoConsulta>
      </div>

      <Modal aberto={Boolean(detalhe)} titulo="Dados do administrador" onFechar={() => setModal(null)}>
        {detalhe && (
          <div className="space-y-5">
            <div className="flex items-center gap-3.5">
              <Avatar nome={detalhe.nome} tamanho="medio" apagado={detalhe.status !== 'Ativo'} />
              <div className="min-w-0 flex-1">
                <p className="break-words text-lg font-extrabold text-cinza-900">{detalhe.nome}</p>
                <p className="text-sm font-bold text-marca-700">{detalhe.perfil}</p>
              </div>
              <Badge>{detalhe.status}</Badge>
            </div>
            <ListaDetalhes
              linhas={[
                { rotulo: 'CPF', valor: mascararCpf(detalhe.cpf), classe: 'tabular-nums' },
                { rotulo: 'E-mail', valor: detalhe.email },
                { rotulo: 'Cadastrado em', valor: formatarData(detalhe.data_cadastro), classe: 'tabular-nums' },
              ]}
            />
            {ehVoce(detalhe) && <Alerta tipo="info">Esta é a sua conta. A desativação da própria conta administrativa não é permitida.</Alerta>}
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Fechar
              </Botao>
              {detalhe.status === 'Ativo' && !ehVoce(detalhe) && (
                <Botao variante="perigoContorno" onClick={() => abrir({ modo: 'desativar', admin: detalhe })}>
                  Desativar
                </Botao>
              )}
              <Botao onClick={() => abrir({ modo: 'editar', admin: detalhe })}>Editar</Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>

      <Modal
        aberto={modal?.modo === 'novo' || modal?.modo === 'editar'}
        titulo={modal?.modo === 'novo' ? 'Cadastrar administrador' : 'Editar administrador'}
        onFechar={() => setModal(null)}
      >
        {(modal?.modo === 'novo' || modal?.modo === 'editar') && (
          <FormularioAdministrador
            inicial={modal.admin}
            salvando={cadastrar.isPending || editar.isPending}
            erro={erroModal}
            aoCancelar={() => setModal(null)}
            aoSalvar={(dados) => (modal.modo === 'editar' ? editar.mutate({ id: modal.admin.id, dados }) : cadastrar.mutate(dados))}
          />
        )}
      </Modal>

      {/* Quadro 18 — desativação */}
      <Modal aberto={modal?.modo === 'desativar'} titulo="Desativar administrador" onFechar={() => setModal(null)}>
        {modal?.modo === 'desativar' && (
          <div className="space-y-5">
            <p className="text-[15px] text-cinza-700">
              Desativar <strong className="text-cinza-900">{modal.admin.nome}</strong> ({modal.admin.perfil})? Novos acessos serão impedidos e as
              sessões ativas, encerradas. O histórico é preservado para auditoria.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao variante="perigo" onClick={() => desativar.mutate(modal.admin.id)} carregando={desativar.isPending}>
                Confirmar desativação
              </Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>
    </div>
  )
}
