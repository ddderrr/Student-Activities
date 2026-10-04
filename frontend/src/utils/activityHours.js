export function validHours(value, allowZero = false) {
  if (value === '' || value === null || value === undefined) return false
  const number = Number(value)
  return Number.isFinite(number) && (allowZero ? number >= 0 : number > 0) &&
    number <= 99999999.99 && /^\d+(\.\d{1,2})?$/.test(String(value))
}
