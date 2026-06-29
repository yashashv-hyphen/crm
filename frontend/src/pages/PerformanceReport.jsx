import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getPerformanceReport, downloadPerformanceReport } from '../api/reports'
import toast from 'react-hot-toast'

export default function PerformanceReport() {
  const [filters, setFilters] = useState({ year: new Date().getFullYear() })
  const [applied, setApplied] = useState(filters)

  const { data, isLoading } = useQuery({
    queryKey: ['performance-report', applied],
    queryFn: () => getPerformanceReport(applied).then((r) => r.data),
  })

  const handleDownload = async () => {
    try {
      const resp = await downloadPerformanceReport(applied)
      const url = URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'performance_report.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
    }
  }

  const rows = data?.rows || []
  const totals = data?.totals

  const allActivities = rows[0]?.metrics?.map((m) => m.activity_name) || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Performance Report</h1>
        <button onClick={handleDownload} className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700">
          Download Excel
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex gap-4 items-end flex-wrap">
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
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input type="date" value={filters.from_date || ''} onChange={(e) => setFilters((f) => ({ ...f, from_date: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input type="date" value={filters.to_date || ''} onChange={(e) => setFilters((f) => ({ ...f, to_date: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm" />
        </div>
        <button onClick={() => setApplied({ ...filters })} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700">
          Apply
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading report...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-5 py-3 text-left">Agent</th>
                  {allActivities.flatMap((name) => [
                    <th key={`${name}-a`} className="px-3 py-3 text-right">{name}<br /><span className="text-gray-400 normal-case font-normal">Assigned</span></th>,
                    <th key={`${name}-m`} className="px-3 py-3 text-right"><br /><span className="text-gray-400 normal-case font-normal">Moved</span></th>,
                    <th key={`${name}-p`} className="px-3 py-3 text-right"><br /><span className="text-gray-400 normal-case font-normal">%</span></th>,
                  ])}
                  <th className="px-5 py-3 text-right">Avg Days</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {rows.map((row) => (
                  <tr key={row.fos_id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium">{row.fos_name}</td>
                    {row.metrics.flatMap((m, i) => [
                      <td key={`${i}-a`} className="px-3 py-3 text-right">{m.total_assigned?.toLocaleString()}</td>,
                      <td key={`${i}-m`} className="px-3 py-3 text-right">{m.total_moved?.toLocaleString()}</td>,
                      <td key={`${i}-p`} className="px-3 py-3 text-right font-medium text-blue-700">{m.movement_pct?.toFixed(1)}%</td>,
                    ])}
                    <td className="px-5 py-3 text-right">{row.overall_avg_days?.toFixed(1) ?? '—'}</td>
                  </tr>
                ))}
                {totals && (
                  <tr className="bg-gray-50 font-semibold">
                    <td className="px-5 py-3">TOTAL</td>
                    {totals.metrics.flatMap((m, i) => [
                      <td key={`t-${i}-a`} className="px-3 py-3 text-right">{m.total_assigned?.toLocaleString()}</td>,
                      <td key={`t-${i}-m`} className="px-3 py-3 text-right">{m.total_moved?.toLocaleString()}</td>,
                      <td key={`t-${i}-p`} className="px-3 py-3 text-right text-blue-700">{m.movement_pct?.toFixed(1)}%</td>,
                    ])}
                    <td className="px-5 py-3 text-right">{totals.overall_avg_days?.toFixed(1) ?? '—'}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
