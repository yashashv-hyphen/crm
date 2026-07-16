const NEGATIVE_VALUES = new Set([
  'no', 'n', '0', 'false', 'na', 'n/a', 'none', '-', 'pending', 'inactive', 'not launched', 'not done',
])

export function isDone(value) {
  if (value === null || value === undefined) return false
  if (typeof value === 'number') return value !== 0
  const normalized = String(value).trim().toLowerCase()
  if (!normalized) return false
  return !NEGATIVE_VALUES.has(normalized)
}

export function TickCross({ value }) {
  const done = isDone(value)
  return (
    <span
      className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold ${
        done ? 'bg-green-100 text-green-700' : 'bg-red-50 text-red-500'
      }`}
      title={done ? String(value) : 'Not done'}
    >
      {done ? '✔' : '✖'}
    </span>
  )
}
