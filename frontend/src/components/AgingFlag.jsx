const COLOR_MAP = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-400',
  orange: 'bg-orange-500',
  red: 'bg-red-600',
}

const LABEL_MAP = {
  green: 'Fresh (0-7d)',
  yellow: 'Aging (8-14d)',
  orange: 'Old (15-21d)',
  red: 'Critical (21+d)',
}

export default function AgingFlag({ color }) {
  if (!color) return null
  return (
    <span
      title={LABEL_MAP[color]}
      className={`inline-block w-3 h-3 rounded-full ${COLOR_MAP[color] || 'bg-gray-300'}`}
    />
  )
}
