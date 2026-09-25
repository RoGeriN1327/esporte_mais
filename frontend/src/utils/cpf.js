export function somenteDigitos(valor) {
  return (valor || '').replace(/\D/g, '')
}

export function mascararCpf(valor) {
  const digitos = somenteDigitos(valor).slice(0, 11)
  return digitos
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d{1,2})$/, '.$1-$2')
}

export function cpfValido(valor) {
  const cpf = somenteDigitos(valor)
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false
  for (const posicao of [9, 10]) {
    let soma = 0
    for (let j = 0; j < posicao; j += 1) soma += Number(cpf[j]) * (posicao + 1 - j)
    let digito = (soma * 10) % 11
    if (digito === 10) digito = 0
    if (digito !== Number(cpf[posicao])) return false
  }
  return true
}
