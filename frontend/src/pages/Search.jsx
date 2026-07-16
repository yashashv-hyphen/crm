import { useState } from 'react'
import { searchLeads } from '../api/leads'
import LeadTable from '../components/LeadTable'
import LeadDetailDrawer from '../components/LeadDetailDrawer'

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedLead, setSelectedLead] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const { data } = await searchLeads(query)
      setResults(Array.isArray(data) ? data : (data.items ?? []))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-gray-800">Search Leads</h1>
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by Phone or Merchant ID — comma-separated for multiple"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results && (
        <LeadTable
          data={{ items: results, total: results.length, page: 1, pages: 1, size: results.length }}
          loading={false}
          page={1}
          pages={1}
          total={results.length}
          size={results.length}
          onPageChange={() => {}}
          onLeadClick={setSelectedLead}
        />
      )}

      {selectedLead && (
        <LeadDetailDrawer
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onSaved={() => setSelectedLead(null)}
        />
      )}
    </div>
  )
}
