import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import { Alerta, Badge, Botao, Campo, Carregando, Modal, classesDeInput } from '../../components/ui'
import { useAuth } from '../../contexts/AuthContext'
import { cpfValido, mascararCpf } from '../../utils/cpf'

export default function AdministradoresPage() {
  const queryClient = useQueryClient()
  const { usuario: usuarioLogado } = useAuth()
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm()

  const { data: administradores, isLoading } = useQuery({
    queryKey: ['admin-administradores'],
    queryFn: adminApi.listarAdministradores,
  })

  useEffect(() => {
    if (modal?.modo === 'editar' && modal.admin) {
      reset({
        nome: modal.admin.nome,
        cpf: mascararCpf(modal.admin.cpf),
        email: modal.admin.email,
        perfil: modal.admin.perfil,
      })
    } else if (modal?.modo === 'novo') {
      reset({ nome: '', cpf: '', email: '', perfil: '' })
    }
  }, [modal, reset])

  function aoMutacaoConcluida(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setErroModal('')
        setModal(null)
        queryClient.invalidateQueries({ queryKey: ['admin-administradores'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const cadastrar = useMutation({
    mutationFn: adminApi.cadastrarAdministrador,
    ...aoMutacaoConcluida('Administrador cadastrado. A senha temporária foi enviada por e-mail.'),
  })
  const editar = useMutation({
    mutationFn: ({ id, dados }) => adminApi.editarAdministrador(id, dados),
    ...aoMutacaoConcluida('Administrador atualizado. Troca de perfil vale na próxima sessão.'),
  })
  const desativar = useMutation({
    mutationFn: (id) => adminApi.desativarAdministrador(id),
    ...aoMutacaoConcluida('Administrador desativado; sessões ativas foram invalidadas.'),
  })

  function aoSalvar(dados) {
    if (modal?.modo === 'editar') {
      editar.mutate({ id: modal.admin.id, dados })
    } else {
      cadastrar.mutate(dados)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Gerenciar administradores</h1>
        <Botao onClick={() => { setErroModal(''); setModal({ modo: 'novo' }) }}>
          Cadastrar Administrador
        </Botao>
      </div>

      <Alerta tipo="sucesso">{mensagem}</Alerta>

      {isLoading ? (
        <Carregando />
      ) : (
        <div className="overflow-x-auto rounded-xl bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">E-mail</th>
                <th className="px-4 py-3">Perfil</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {(administradores || []).map((admin) => (
                <tr key={admin.id}>
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {admin.nome}
                    {admin.id === usuarioLogado?.id && (
                      <span className="ml-2 text-xs text-gray-400">(você)</span>
                    )}
                  </td>
                  <td className="px-4 py-3">{admin.email}</td>
                  <td className="px-4 py-3">{admin.perfil}</td>
                  <td className="px-4 py-3"><Badge>{admin.status}</Badge></td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <Botao
                        variante="secundario"
                        onClick={() => { setErroModal(''); setModal({ modo: 'editar', admin }) }}
                      >
                        Editar
                      </Botao>
                      {}
                      {admin.status === 'Ativo' && admin.id !== usuarioLogado?.id && (
                        <Botao
                          variante="perigo"
                          onClick={() => { setErroModal(''); setModal({ modo: 'desativar', admin }) }}
                        >
                          Desativar
                        </Botao>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {}
      <Modal
        aberto={modal?.modo === 'novo' || modal?.modo === 'editar'}
        titulo={modal?.modo === 'novo' ? 'Cadastrar administrador' : 'Editar administrador'}
        onFechar={() => setModal(null)}
      >
        <form className="space-y-4" onSubmit={handleSubmit(aoSalvar)} noValidate>
          <Campo label="Nome Completo" erro={errors.nome?.message}>
            <input
              className={classesDeInput(errors.nome)}
              maxLength={100}
              {...register('nome', { required: 'Informe o nome completo.' })}
            />
          </Campo>
          <Campo label="CPF" erro={errors.cpf?.message}>
            <input
              className={classesDeInput(errors.cpf)}
              inputMode="numeric"
              placeholder="000.000.000-00"
              {...register('cpf', {
                required: 'Informe o CPF.',
                validate: (valor) => cpfValido(valor) || 'CPF inválido. Informe 11 dígitos numéricos válidos.',
                onChange: (evento) => setValue('cpf', mascararCpf(evento.target.value)),
              })}
            />
          </Campo>
          <Campo label="E-mail" erro={errors.email?.message}>
            <input
              type="email"
              className={classesDeInput(errors.email)}
              {...register('email', {
                required: 'Informe o e-mail.',
                pattern: { value: /.+@.+\..+/, message: 'Informe um e-mail válido.' },
              })}
            />
          </Campo>
          {}
          <Campo label="Perfil" erro={errors.perfil?.message}>
            <select
              className={classesDeInput(errors.perfil)}
              {...register('perfil', { required: 'Selecione o perfil.' })}
            >
              <option value="">Selecione...</option>
              <option value="Operador">Operador</option>
              <option value="Gestor">Gestor</option>
            </select>
          </Campo>
          {modal?.modo === 'novo' && (
            <p className="text-xs text-gray-500">
              Uma senha temporária será gerada e enviada por e-mail ao novo administrador.
            </p>
          )}
          <Alerta tipo="erro">{erroModal}</Alerta>
          <div className="flex justify-end gap-3">
            <Botao type="button" variante="secundario" onClick={() => setModal(null)}>
              Cancelar
            </Botao>
            <Botao type="submit" carregando={cadastrar.isPending || editar.isPending}>
              Salvar
            </Botao>
          </div>
        </form>
      </Modal>

      {}
      <Modal aberto={modal?.modo === 'desativar'} titulo="Desativar administrador" onFechar={() => setModal(null)}>
        {modal?.admin && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Desativar <strong>{modal.admin.nome}</strong> ({modal.admin.perfil})? Novos acessos
              serão impedidos e as sessões ativas invalidadas. O histórico é preservado para
              auditoria.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao
                variante="perigo"
                onClick={() => desativar.mutate(modal.admin.id)}
                carregando={desativar.isPending}
              >
                Confirmar desativação
              </Botao>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
