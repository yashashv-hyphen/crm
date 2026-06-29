const STATUS_STYLES = {
  overdue: 'bg-red-100 text-red-700',
  today: 'bg-orange-100 text-orange-700',
  upcoming: 'bg-yellow-100 text-yellow-700',
  future: 'bg-green-100 text-green-700',
}

const STATUS_ICONS = {
  overdue: '🔴',
  today: '🟠',
  upcoming: '🟡',
  future: '🟢',
}

export default function FollowUpBadge({ date, status }) {
  if (!date) return null
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[status] || ''}`}>
      {STATUS_ICONS[status]} {date}
    </span>
  )
}
