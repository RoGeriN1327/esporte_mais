// Aviso de cold start: aparece quando alguma requisição à API passa de 3 segundos
// (ver api/lentidao.js) e some quando ela termina. Fica em todas as telas.
import { useSyncExternalStore } from 'react'

import { assinar, haRequisicaoLenta } from '../api/lentidao'
import { Spinner } from './ui'

export default function AvisoLentidao() {
  const lento = useSyncExternalStore(assinar, haRequisicaoLenta)

  // A região "status" fica sempre no DOM (vazia quando não há lentidão) para que o
  // leitor de tela anuncie o aviso no momento em que o texto aparece.
  return (
    <div role="status" aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      {lento && (
        <div className="pointer-events-auto flex max-w-md items-start gap-3 rounded-xl border border-marca-200 bg-white px-4 py-3 text-sm shadow-lg">
          <span className="mt-0.5 text-marca-600">
            <Spinner pequeno />
          </span>
          <div>
            <p className="font-bold text-cinza-900">Inicializando serviços esportivos, aguarde um instante...</p>
            <p className="mt-0.5 text-cinza-600">
              O sistema estava em repouso e pode levar até 1 minuto para responder.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
