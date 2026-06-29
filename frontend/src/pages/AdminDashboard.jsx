import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getAdminDashboard } from '../api/dashboard'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ year: new Date().getFullYear() })
  const [appliedFilters, setAppliedFilters] = useState(filters)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard', appliedFilters],
    queryFn: () => getAdminDashboard(appliedFilters).then((r) => r.data),
    refetchInterval: 30_000,
  })

  const drillDown = (activityId, fosId) => {
    const params = new URLSearchParams()
    if (activityId) params.set('activity_id', activityId)
    if (fosId) params.set('fos_id', fosId)
    navigate(`/leads?${params}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Admin Dashboard</h1>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-end gap-4 flex-wrap">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Year</label>
          <input
            type="number"
            value={filters.year || ''}
            onChange={(e) => setFilters((f) => ({ ...f, year: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm w-24"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">From Date</label>
          <input
            type="date"
            value={filters.from_date || ''}
            onChange={(e) => setFilters((f) => ({ ...f, from_date: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To Date</label>
          <input
            type="date"
            value={filters.to_date || ''}
            onChange={(e) => setFilters((f) => ({ ...f, to_date: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          />
        </div>
        <button
          onClick={() => setAppliedFilters({ ...filters })}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700"
        >
          Apply
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : (
        <>
          {/* Overall Stage Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-700">Overall Stage Summary (All Agents)</h2>
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
                {(data?.overall_stage_summary || []).map((row) => (
                  <tr key={row.activity_id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium">{row.activity_name}</td>
                    <td className="px-5 py-3 text-right">
                      <button onClick={() => drillDown(row.activity_id)} className="text-blue-600 hover:underline font-semibold">
                        {row.total_assigned?.toLocaleString()}
                      </button>
                    </td>
                    <td className="px-5 py-3 text-right text-gray-700">{row.moved_to_next?.toLocaleString()}</td>
                    <td className="px-5 py-3 text-right text-gray-700">{row.pending?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Agent-wise Breakdown */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-700">Agent-wise Breakdown</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-5 py-3 text-left">Agent</th>
                    {(data?.overall_stage_summary || []).map((s) => (
                      <th key={s.activity_id} className="px-3 py-3 text-right" colSpan={2}>
                        {s.activity_name}
                      </th>
                    ))}
                  </tr>
                  <tr>
                    <th className="px-5 py-3"></th>
                    {(data?.overall_stage_summary || []).flatMap((s) => [
                      <th key={`${s.activity_id}-a`} className="px-3 py-2 text-right text-xs">Assigned</th>,
                      <th key={`${s.activity_id}-m`} className="px-3 py-2 text-right text-xs">Moved</th>,
                    ])}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(data?.agent_wise_summary || []).map((agent) => (
                    <tr key={agent.fos_id} className="hover:bg-gray-50">
                      <td className="px-5 py-3">
                        <button onClick={() => drillDown(null, agent.fos_id)} className="text-blue-600 hover:underline font-medium">
                          {agent.fos_name}
                        </button>
                      </td>
                      {agent.stage_summary.flatMap((s) => [
                        <td key={`${s.activity_id}-a`} className="px-3 py-3 text-right">{s.total_assigned?.toLocaleString()}</td>,
                        <td key={`${s.activity_id}-m`} className="px-3 py-3 text-right">{s.moved_to_next?.toLocaleString()}</td>,
                      ])}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
