import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getLeads, downloadLeads } from '../api/leads'
import LeadTable from '../components/LeadTable'
import LeadDetailDrawer from '../components/LeadDetailDrawer'
import toast from 'react-hot-toast'

export default function LeadTablePage() {
  const [searchParams] = useSearchParams()
  const [page, setPage] = useState(1)
  const [selectedLead, setSelectedLead] = useState(null)
  const [filters, setFilters] = useState({
    activity_id: searchParams.get('activity_id') || '',
    fos_id: searchParams.get('fos_id') || '',
    current_stage: '',
    is_archived: false,
  })

  const queryParams = { ...filters, page, size: 50 }
  Object.keys(queryParams).forEach((k) => !queryParams[k] && delete queryParams[k])

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['leads', queryParams],
    queryFn: () => getLeads(queryParams).then((r) => r.data),
    refetchInterval: 30_000,
  })

  const handleDownload = async () => {
    try {
      const resp = await downloadLeads(queryParams)
      const url = URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'leads_export.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Leads</h1>
        <button
          onClick={handleDownload}
          className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700"
        >
          Download Excel
        </button>
      </div>

      {/* Quick filters */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex gap-4 flex-wrap items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Current Stage</label>
          <input
            type="text"
            value={filters.current_stage}
            onChange={(e) => setFilters((f) => ({ ...f, current_stage: e.target.value }))}
            placeholder="Filter by stage..."
            className="border border-gray-300 rounded px-2 py-1 text-sm w-40"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={filters.is_archived}
            onChange={(e) => setFilters((f) => ({ ...f, is_archived: e.target.checked }))}
          />
          Show Archived
        </label>
        <button
          onClick={() => { setPage(1); refetch() }}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700"
        >
          Apply
        </button>
      </div>

      <LeadTable
        data={data}
        loading={isLoading}
        page={page}
        pages={data?.pages || 1}
        total={data?.total || 0}
        size={50}
        onPageChange={setPage}
        refetch={refetch}
        onLeadClick={setSelectedLead}
      />

      {selectedLead && (
        <LeadDetailDrawer
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onSaved={() => refetch()}
        />
      )}
    </div>
  )
}
