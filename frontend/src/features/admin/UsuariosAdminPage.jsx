// Gerenciar usuários (RF001: A7 cadastrar, A8 desativar e A9 reativar Usuário Pessoa pelo
// Operador ou Gestor; Quadros 19 a 22 do DERS). A consulta carrega a lista ao clicar em "Buscar"
// e filtra por nome, CPF e status no navegador (a API devolve a lista completa).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { TbUserPlus, TbUserSearch } from 'react-icons/tb'

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
import { useConsulta } from '../../hooks/useConsulta'
import { cpfValido, mascararCpf, somenteDigitos } from '../../utils/cpf'
import { formatarData } from '../../utils/datas'
import { normalizarTexto } from '../../utils/texto'

const CHAVES = ['nome', 'cpf', 'status']

function filtrar(usuarios, { nome, cpf, status }) {
  const termo = normalizarTexto(nome)
  const digitos = somenteDigitos(cpf)
  return usuarios.filter(
    (usuario) =>
      (!termo || normalizarTexto(usuario.nome).includes(termo)) &&
      (!digitos || usuario.cpf.includes(digitos)) &&
      (!status || usuario.status === status),
  )
}

function FormularioUsuario({ aoSalvar, aoCancelar, salvando, erro }) {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm()
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
      <Campo label="E-mail" erro={errors.email?.message} dica="O cidadão recebe neste e-mail a senha de acesso gerada pelo sistema.">
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

export default function UsuariosAdminPage() {
  const queryClient = useQueryClient()
  const consulta = useConsulta(CHAVES)
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)

  const { data: todos, isFetching, isError } = useQuery({
    queryKey: ['admin-usuarios-pessoa'],
    queryFn: adminApi.listarUsuariosPessoa,
    enabled: consulta.consultado,
  })
  const usuarios = todos ? filtrar(todos, consulta.filtros) : undefined

  function abrir(config) {
    setErroModal('')
    setModal(config)
  }

  function aoTerminar(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-usuarios-pessoa'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const cadastrar = useMutation({
    mutationFn: adminApi.cadastrarUsuarioPessoa,
    ...aoTerminar('Usuário cadastrado. A senha de acesso foi enviada para o e-mail informado.'),
  })
  const desativar = useMutation({ mutationFn: (id) => adminApi.desativarUsuarioPessoa(id), ...aoTerminar('Usuário desativado com sucesso.') })
  const reativar = useMutation({ mutationFn: (id) => adminApi.reativarUsuarioPessoa(id), ...aoTerminar('Usuário reativado. O acesso volta a funcionar com as credenciais anteriores.') })

  const detalhe = modal?.modo === 'detalhes' ? modal.usuario : null

  return (
    <div>
      <CabecalhoPagina
        voltarPara="/admin"
        voltarTexto="Início"
        titulo="Gerenciar usuários"
        descricao="Consulte os cidadãos cadastrados. Abra um usuário para ver os dados, desativar ou reativar a conta."
        acoes={
          <Botao onClick={() => abrir({ modo: 'novo' })}>
            <TbUserPlus aria-hidden="true" className="size-[18px]" />
            Cadastrar Usuário
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
          <Campo label="CPF">
            <input
              name="cpf"
              defaultValue={consulta.filtros.cpf}
              inputMode="numeric"
              autoComplete="off"
              placeholder="000.000.000-00"
              onChange={(evento) => (evento.target.value = mascararCpf(evento.target.value))}
              className={`${classesDeInput(false)} tabular-nums`}
            />
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
          erro={isError && 'Não foi possível buscar os usuários. Tente novamente em instantes.'}
          vazio={!usuarios?.length}
          inicial={{
            Icone: TbUserSearch,
            titulo: 'Consulte os usuários',
            descricao: 'Filtre por nome, CPF ou status e clique em “Buscar”. Para listar todos, clique em “Buscar” sem preencher nada.',
          }}
          textoCarregando="Buscando usuários…"
          tituloVazio="Nenhum usuário encontrado"
          descricaoVazio="Não há usuários com esses filtros. Altere a busca ou use “Limpar filtros” para ver todos."
        >
          <ListaClicavel titulo="Usuários" total={usuarios?.length} rotuloSingular="usuário" rotuloPlural="usuários">
            {usuarios?.map((usuario) => (
              <ItemClicavel key={usuario.id} onClick={() => abrir({ modo: 'detalhes', usuario })}>
                <Avatar nome={usuario.nome} tamanho="medio" apagado={usuario.status !== 'Ativo'} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-extrabold text-cinza-900">{usuario.nome}</span>
                  <span className="mt-0.5 block truncate text-sm text-cinza-600">
                    <span className="tabular-nums">{mascararCpf(usuario.cpf)}</span> · {usuario.email}
                  </span>
                </span>
                <Badge>{usuario.status}</Badge>
              </ItemClicavel>
            ))}
          </ListaClicavel>
        </ResultadoConsulta>
      </div>

      <Modal aberto={Boolean(detalhe)} titulo="Dados do usuário" onFechar={() => setModal(null)}>
        {detalhe && (
          <div className="space-y-5">
            <div className="flex items-center gap-3.5">
              <Avatar nome={detalhe.nome} tamanho="medio" apagado={detalhe.status !== 'Ativo'} />
              <p className="min-w-0 flex-1 break-words text-lg font-extrabold text-cinza-900">{detalhe.nome}</p>
              <Badge>{detalhe.status}</Badge>
            </div>
            <ListaDetalhes
              linhas={[
                { rotulo: 'CPF', valor: mascararCpf(detalhe.cpf), classe: 'tabular-nums' },
                { rotulo: 'E-mail', valor: detalhe.email },
                { rotulo: 'Cadastrado em', valor: formatarData(detalhe.data_cadastro), classe: 'tabular-nums' },
              ]}
            />
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Fechar
              </Botao>
              {detalhe.status === 'Ativo' ? (
                <Botao variante="perigoContorno" onClick={() => abrir({ modo: 'desativar', usuario: detalhe })}>
                  Desativar
                </Botao>
              ) : (
                <Botao onClick={() => abrir({ modo: 'reativar', usuario: detalhe })}>Reativar</Botao>
              )}
            </BarraAcoes>
          </div>
        )}
      </Modal>

      <Modal aberto={modal?.modo === 'novo'} titulo="Cadastrar usuário" onFechar={() => setModal(null)}>
        {modal?.modo === 'novo' && (
          <FormularioUsuario
            aoSalvar={(dados) => cadastrar.mutate(dados)}
            aoCancelar={() => setModal(null)}
            salvando={cadastrar.isPending}
            erro={erroModal}
          />
        )}
      </Modal>

      {/* Quadro 21 — desativação */}
      <Modal aberto={modal?.modo === 'desativar'} titulo="Desativar usuário" onFechar={() => setModal(null)}>
        {modal?.modo === 'desativar' && (
          <div className="space-y-5">
            <Alerta tipo="aviso">
              Os agendamentos com status “Confirmado” deste usuário serão cancelados automaticamente, e ele será notificado por e-mail.
            </Alerta>
            <p className="text-[15px] text-cinza-700">
              Confirma a desativação de <strong className="text-cinza-900">{modal.usuario.nome}</strong>? O histórico é preservado.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao variante="perigo" onClick={() => desativar.mutate(modal.usuario.id)} carregando={desativar.isPending}>
                Confirmar desativação
              </Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>

      {/* Quadro 22 — reativação */}
      <Modal aberto={modal?.modo === 'reativar'} titulo="Reativar usuário" onFechar={() => setModal(null)}>
        {modal?.modo === 'reativar' && (
          <div className="space-y-5">
            <p className="text-[15px] text-cinza-700">
              Reativar <strong className="text-cinza-900">{modal.usuario.nome}</strong>? O login volta a funcionar imediatamente, com as
              credenciais anteriores.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <BarraAcoes>
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao onClick={() => reativar.mutate(modal.usuario.id)} carregando={reativar.isPending}>
                Confirmar reativação
              </Botao>
            </BarraAcoes>
          </div>
        )}
      </Modal>
    </div>
  )
}
