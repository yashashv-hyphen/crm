import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getFosDashboard } from '../api/dashboard'
import { useAuth } from '../context/AuthContext'

function ClickableNumber({ value, onClick }) {
  return (
    <button onClick={onClick} className="text-blue-600 hover:underline font-semibold">
      {value?.toLocaleString()}
    </button>
  )
}

export default function FosDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['fos-dashboard'],
    queryFn: () => getFosDashboard().then((r) => r.data),
    refetchInterval: 30_000,
  })

  const goToLeads = (activityId, status) => {
    const params = new URLSearchParams()
    if (activityId) params.set('activity_id', activityId)
    if (status === 'moved') params.set('has_final_stage', 'true')
    if (status === 'pending') params.set('has_final_stage', 'false')
    navigate(`/leads?${params}`)
  }

  if (isLoading) return <div className="text-center py-12 text-gray-400">Loading...</div>

  const followUpCount = data?.follow_up_today_count || 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Welcome, {user?.full_name}</h1>
        {followUpCount > 0 && (
          <button
            onClick={() => navigate('/follow-ups')}
            className="flex items-center gap-2 bg-red-50 text-red-700 border border-red-200 rounded-lg px-4 py-2 text-sm font-medium hover:bg-red-100"
          >
            🔴 {followUpCount} follow-up{followUpCount !== 1 ? 's' : ''} due today
          </button>
        )}
      </div>

      {/* Stage Summary Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">Stage Summary</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">Stage</th>
              <th className="px-5 py-3 text-right">Total Assigned</th>
              <th className="px-5 py-3 text-right">Moved to Next</th>
              <th className="px-5 py-3 text-right">Pending</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {(data?.stage_summary || []).map((row) => (
              <tr key={row.activity_id} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-800">{row.activity_name}</td>
                <td className="px-5 py-3 text-right">
                  <ClickableNumber value={row.total_assigned} onClick={() => goToLeads(row.activity_id, 'all')} />
                </td>
                <td className="px-5 py-3 text-right">
                  <ClickableNumber value={row.moved_to_next} onClick={() => goToLeads(row.activity_id, 'moved')} />
                </td>
                <td className="px-5 py-3 text-right">
                  <ClickableNumber value={row.pending} onClick={() => goToLeads(row.activity_id, 'pending')} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Disposition Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">Disposition Summary</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">Sub-Disposition</th>
              <th className="px-5 py-3 text-right">This Week</th>
              <th className="px-5 py-3 text-right">YTD</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {(data?.disposition_summary || []).map((row, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-700">{row.sub_disposition}</td>
                <td className="px-5 py-3 text-right text-gray-700">{row.this_week?.toLocaleString()}</td>
                <td className="px-5 py-3 text-right text-gray-700">{row.ytd?.toLocaleString()}</td>
              </tr>
            ))}
            {!data?.disposition_summary?.length && (
              <tr><td colSpan={3} className="px-5 py-4 text-center text-gray-400">No disposition data yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
