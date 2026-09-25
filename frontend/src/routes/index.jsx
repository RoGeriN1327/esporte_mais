import { Navigate, Outlet, Route, Routes } from 'react-router-dom'

import Layout from '../components/Layout'
import { Carregando } from '../components/ui'
import { useAuth } from '../contexts/AuthContext'
import CadastroPage from '../features/auth/CadastroPage'
import LoginPage from '../features/auth/LoginPage'
import RecuperarSenhaPage from '../features/auth/RecuperarSenhaPage'
import RedefinirSenhaPage from '../features/auth/RedefinirSenhaPage'
import HomeAdminPage from '../features/home/HomeAdminPage'
import HomePessoaPage from '../features/home/HomePessoaPage'
import PerfilPage from '../features/perfil/PerfilPage'
import AgendarPage from '../features/agendamentos/AgendarPage'
import MeusAgendamentosPage from '../features/agendamentos/MeusAgendamentosPage'
import QuadrasPage from '../features/agendamentos/QuadrasPage'
import AdministradoresPage from '../features/admin/AdministradoresPage'
import ConfiguracoesPage from '../features/admin/ConfiguracoesPage'
import PainelAgendamentosPage from '../features/admin/PainelAgendamentosPage'
import QuadrasAdminPage from '../features/admin/QuadrasAdminPage'
import UsuariosAdminPage from '../features/admin/UsuariosAdminPage'

function destinoDe(usuario) {
  return usuario?.tipo === 'Administrativo' ? '/admin' : '/'
}

function RotaPublica() {
  const { usuario, carregando } = useAuth()
  if (carregando) return <Carregando />
  if (usuario) return <Navigate to={destinoDe(usuario)} replace />
  return <Outlet />
}

function RotaPessoa() {
  const { usuario, carregando, ehPessoa } = useAuth()
  if (carregando) return <Carregando />
  if (!usuario) return <Navigate to="/login" replace />
  if (!ehPessoa) return <Navigate to="/admin" replace />
  return <Outlet />
}

function RotaAdmin() {
  const { usuario, carregando, ehAdmin } = useAuth()
  if (carregando) return <Carregando />
  if (!usuario) return <Navigate to="/login" replace />
  if (!ehAdmin) return <Navigate to="/" replace />
  return <Outlet />
}

function RotaGestor() {
  const { ehGestor } = useAuth()
  if (!ehGestor) return <Navigate to="/admin" replace />
  return <Outlet />
}

export default function Rotas() {
  return (
    <Routes>
      <Route element={<RotaPublica />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/cadastro" element={<CadastroPage />} />
        <Route path="/recuperar-senha" element={<RecuperarSenhaPage />} />
        <Route path="/redefinir-senha" element={<RedefinirSenhaPage />} />
      </Route>

      <Route element={<RotaPessoa />}>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePessoaPage />} />
          <Route path="/perfil" element={<PerfilPage />} />
          <Route path="/quadras" element={<QuadrasPage />} />
          <Route path="/quadras/:id/agendar" element={<AgendarPage />} />
          <Route path="/meus-agendamentos" element={<MeusAgendamentosPage />} />
        </Route>
      </Route>

      <Route element={<RotaAdmin />}>
        <Route element={<Layout />}>
          <Route path="/admin" element={<HomeAdminPage />} />
          <Route path="/admin/quadras" element={<QuadrasAdminPage />} />
          <Route path="/admin/agendamentos" element={<PainelAgendamentosPage />} />
          <Route path="/admin/usuarios" element={<UsuariosAdminPage />} />
          <Route element={<RotaGestor />}>
            <Route path="/admin/administradores" element={<AdministradoresPage />} />
            <Route path="/admin/configuracoes" element={<ConfiguracoesPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
