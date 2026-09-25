import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import * as adminApi from '../../api/admin.api'
import { mensagemDeErro } from '../../api/client'
import { Alerta, Badge, Botao, Campo, Carregando, Modal, classesDeInput } from '../../components/ui'
import { cpfValido, mascararCpf } from '../../utils/cpf'

export default function UsuariosAdminPage() {
  const queryClient = useQueryClient()
  const [mensagem, setMensagem] = useState('')
  const [erroModal, setErroModal] = useState('')
  const [modal, setModal] = useState(null)
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm()

  const { data: usuarios, isLoading } = useQuery({
    queryKey: ['admin-usuarios-pessoa'],
    queryFn: adminApi.listarUsuariosPessoa,
  })

  function aoMutacaoConcluida(mensagemSucesso) {
    return {
      onSuccess: () => {
        setMensagem(mensagemSucesso)
        setErroModal('')
        setModal(null)
        reset()
        queryClient.invalidateQueries({ queryKey: ['admin-usuarios-pessoa'] })
      },
      onError: (excecao) => setErroModal(mensagemDeErro(excecao)),
    }
  }

  const cadastrar = useMutation({
    mutationFn: adminApi.cadastrarUsuarioPessoa,
    ...aoMutacaoConcluida('Usuário cadastrado. A senha de acesso foi enviada por e-mail.'),
  })

  const desativar = useMutation({
    mutationFn: (id) => adminApi.desativarUsuarioPessoa(id),
    ...aoMutacaoConcluida('Usuário desativado com sucesso.'),
  })

  const reativar = useMutation({
    mutationFn: (id) => adminApi.reativarUsuarioPessoa(id),
    ...aoMutacaoConcluida('Usuário reativado com sucesso.'),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-800">Gerenciar usuários</h1>
        <Botao onClick={() => { setErroModal(''); setModal({ modo: 'novo' }) }}>Cadastrar Usuário</Botao>
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
                <th className="px-4 py-3">CPF</th>
                <th className="px-4 py-3">E-mail</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {(usuarios || []).map((usuario) => (
                <tr key={usuario.id}>
                  <td className="px-4 py-3 font-medium text-gray-800">{usuario.nome}</td>
                  <td className="px-4 py-3">{mascararCpf(usuario.cpf)}</td>
                  <td className="px-4 py-3">{usuario.email}</td>
                  <td className="px-4 py-3"><Badge>{usuario.status}</Badge></td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {usuario.status === 'Ativo' ? (
                        <Botao
                          variante="perigo"
                          onClick={() => { setErroModal(''); setModal({ modo: 'desativar', usuario }) }}
                        >
                          Desativar
                        </Botao>
                      ) : (
                        <Botao
                          onClick={() => { setErroModal(''); setModal({ modo: 'reativar', usuario }) }}
                        >
                          Reativar
                        </Botao>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(usuarios || []).length === 0 && (
            <p className="py-8 text-center text-gray-500">Nenhum usuário cadastrado.</p>
          )}
        </div>
      )}

      {}
      <Modal aberto={modal?.modo === 'novo'} titulo="Cadastrar usuário" onFechar={() => setModal(null)}>
        <form className="space-y-4" onSubmit={handleSubmit((dados) => cadastrar.mutate(dados))} noValidate>
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
          <p className="text-xs text-gray-500">
            Uma senha aleatória será gerada e enviada por e-mail de boas-vindas ao usuário.
          </p>
          <Alerta tipo="erro">{erroModal}</Alerta>
          <div className="flex justify-end gap-3">
            <Botao type="button" variante="secundario" onClick={() => { setModal(null); reset() }}>
              Cancelar
            </Botao>
            <Botao type="submit" carregando={cadastrar.isPending}>
              Salvar
            </Botao>
          </div>
        </form>
      </Modal>

      {}
      <Modal aberto={modal?.modo === 'desativar'} titulo="Desativar usuário" onFechar={() => setModal(null)}>
        {modal?.usuario && (
          <div className="space-y-4">
            <Alerta tipo="aviso">
              Os agendamentos com status "Confirmado" deste usuário serão cancelados
              automaticamente e ele será notificado por e-mail.
            </Alerta>
            <p className="text-sm text-gray-600">
              Confirmar a desativação de <strong>{modal.usuario.nome}</strong>?
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao
                variante="perigo"
                onClick={() => desativar.mutate(modal.usuario.id)}
                carregando={desativar.isPending}
              >
                Confirmar desativação
              </Botao>
            </div>
          </div>
        )}
      </Modal>

      {}
      <Modal aberto={modal?.modo === 'reativar'} titulo="Reativar usuário" onFechar={() => setModal(null)}>
        {modal?.usuario && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Reativar <strong>{modal.usuario.nome}</strong>? O login volta a funcionar
              imediatamente com as credenciais anteriores.
            </p>
            <Alerta tipo="erro">{erroModal}</Alerta>
            <div className="flex justify-end gap-3">
              <Botao variante="secundario" onClick={() => setModal(null)}>
                Cancelar
              </Botao>
              <Botao onClick={() => reativar.mutate(modal.usuario.id)} carregando={reativar.isPending}>
                Confirmar reativação
              </Botao>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
