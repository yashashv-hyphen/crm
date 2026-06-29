import { useState } from 'react'
import toast from 'react-hot-toast'
import { bulkUpdateLeads } from '../api/leads'
import { useAuth } from '../context/AuthContext'

export default function BulkActionBar({ selectedIds, onDone, activities }) {
  const { user } = useAuth()
  const [subDisposition, setSubDisposition] = useState('')
  const [followUpDate, setFollowUpDate] = useState('')
  const [reassignFosId, setReassignFosId] = useState('')
  const [loading, setLoading] = useState(false)

  if (selectedIds.length === 0) return null

  const apply = async () => {
    const payload = { lead_ids: selectedIds }
    if (subDisposition) payload.sub_disposition = subDisposition
    if (followUpDate) payload.follow_up_date = followUpDate
    if (reassignFosId && user.role === 'admin') payload.assign_to_fos_id = reassignFosId

    if (!confirm(`Update ${selectedIds.length} selected leads?`)) return

    setLoading(true)
    try {
      await bulkUpdateLeads(payload)
      toast.success(`${selectedIds.length} leads updated`)
      onDone()
    } catch {
      toast.error('Bulk update failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg p-4 flex items-center gap-4 z-50">
      <span className="text-sm font-medium text-gray-700">{selectedIds.length} selected</span>
      <input
        type="text"
        placeholder="Sub-disposition..."
        value={subDisposition}
        onChange={(e) => setSubDisposition(e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm w-48"
      />
      <input
        type="date"
        value={followUpDate}
        onChange={(e) => setFollowUpDate(e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm"
      />
      {user?.role === 'admin' && (
        <input
          type="text"
          placeholder="Reassign FOS ID..."
          value={reassignFosId}
          onChange={(e) => setReassignFosId(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm w-48"
        />
      )}
      <button
        onClick={apply}
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Applying...' : 'Apply'}
      </button>
    </div>
  )
}
