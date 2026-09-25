export default function CartaoAuth({ titulo, subtitulo, children }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-800 to-emerald-600 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-center text-3xl font-bold text-emerald-800">
          Esporte<span className="text-emerald-500">+</span>
        </h1>
        <p className="mt-1 text-center text-sm text-gray-500">
          Agendamento de quadras esportivas públicas
        </p>
        <h2 className="mt-6 text-lg font-semibold text-gray-800">{titulo}</h2>
        {subtitulo && <p className="mt-1 text-sm text-gray-500">{subtitulo}</p>}
        <div className="mt-4">{children}</div>
      </div>
    </div>
  )
}
