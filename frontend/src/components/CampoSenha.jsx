// Campo de senha com botão para mostrar/ocultar o que está sendo digitado.
// Aceita o retorno de register() do react-hook-form (por isso o forwardRef).
import { forwardRef, useId, useState } from 'react'
import { TbEye, TbEyeOff } from 'react-icons/tb'

import { classesDeInput } from './estilos'
import { Campo } from './ui'

const CampoSenha = forwardRef(function CampoSenha(
  { label, erro, dica, autoComplete = 'current-password', ...props },
  ref,
) {
  const id = useId()
  const [visivel, setVisivel] = useState(false)

  return (
    <Campo id={id} label={label} erro={erro} dica={dica}>
      <div className="relative">
        <input
          ref={ref}
          id={id}
          type={visivel ? 'text' : 'password'}
          autoComplete={autoComplete}
          spellCheck={false}
          aria-invalid={erro ? true : undefined}
          aria-describedby={erro || dica ? `${id}-mensagem` : undefined}
          className={`${classesDeInput(erro)} pr-11`}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisivel((valor) => !valor)}
          aria-label={visivel ? 'Ocultar senha' : 'Mostrar senha'}
          aria-pressed={visivel}
          className="absolute inset-y-0 right-0 grid w-11 place-items-center rounded-r-lg text-cinza-500 transition-colors hover:text-cinza-800 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-marca-600"
        >
          {visivel ? <TbEyeOff aria-hidden="true" className="size-5" /> : <TbEye aria-hidden="true" className="size-5" />}
        </button>
      </div>
    </Campo>
  )
})

export default CampoSenha
