import { useState, useCallback, useRef } from 'react'
import { updateLead } from '../api/leads'
import AgingFlag from './AgingFlag'
import FollowUpBadge from './FollowUpBadge'
import BulkActionBar from './BulkActionBar'
import Pagination from './Pagination'
import toast from 'react-hot-toast'

function EditableCell({ value, onSave, type = 'text' }) {
  const [editing, setEditing] = useState(false)
  const [localValue, setLocalValue] = useState(value || '')
  const timerRef = useRef(null)

  const handleBlur = () => {
    setEditing(false)
    if (localValue !== (value || '')) {
      clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => onSave(localValue), 500)
    }
  }

  if (!editing) {
    return (
      <span
        onClick={() => setEditing(true)}
        className="cursor-pointer hover:bg-yellow-50 rounded px-1 min-w-[60px] inline-block text-sm"
      >
        {value || <span className="text-gray-400 italic">—</span>}
      </span>
    )
  }

  return (
    <input
      autoFocus
      type={type}
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      onBlur={handleBlur}
      className="border border-blue-400 rounded px-1 py-0 text-sm w-full focus:outline-none"
    />
  )
}

export default function LeadTable({ data, loading, page, pages, total, size, onPageChange, refetch, onLeadClick }) {
  const [selected, setSelected] = useState(new Set())

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === data?.items?.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(data?.items?.map((l) => l.id)))
    }
  }

  const handleSave = useCallback(async (leadId, field, value) => {
    try {
      await updateLead(leadId, { [field]: value || null })
      toast.success('Saved', { duration: 1000 })
      refetch?.()
    } catch {
      toast.error('Save failed')
    }
  }, [refetch])

  const leads = data?.items || []

  if (loading) return <div className="text-center py-12 text-gray-400">Loading leads...</div>
  if (!leads.length) return <div className="text-center py-12 text-gray-400">No leads found for the selected filters.</div>

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
        <table className="min-w-full text-sm divide-y divide-gray-100">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="w-8 px-3 py-3">
                <input type="checkbox" onChange={toggleAll} checked={selected.size === leads.length && leads.length > 0} />
              </th>
              <th className="px-3 py-3 text-left">Aging</th>
              <th className="px-3 py-3 text-left">Merchant ID</th>
              <th className="px-3 py-3 text-left">Seller Name</th>
              <th className="px-3 py-3 text-left">Mobile</th>
              <th className="px-3 py-3 text-left">Activity</th>
              <th className="px-3 py-3 text-left">Current Stage</th>
              <th className="px-3 py-3 text-left">Sub-Disposition</th>
              <th className="px-3 py-3 text-left">Follow-up</th>
              <th className="px-3 py-3 text-left min-w-[200px]">Remark</th>
              <th className="px-3 py-3 text-left">FOS</th>
              <th className="px-3 py-3 text-left">Assignment Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {leads.map((lead) => (
              <tr
                key={lead.id}
                className={`hover:bg-gray-50 transition-colors cursor-pointer ${selected.has(lead.id) ? 'bg-blue-50' : ''}`}
                onClick={() => onLeadClick?.(lead)}
              >
                <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                  <input type="checkbox" checked={selected.has(lead.id)} onChange={() => toggleSelect(lead.id)} />
                </td>
                <td className="px-3 py-2">
                  <AgingFlag color={lead.aging_color} />
                </td>
                <td className="px-3 py-2 font-mono text-xs text-gray-700">
                  {lead.merchant_id}
                  {lead.is_self_created && (
                    <span className="ml-1.5 inline-block bg-green-100 text-green-700 text-[10px] font-semibold px-1.5 py-0.5 rounded">NR</span>
                  )}
                </td>
                <td className="px-3 py-2">{lead.seller_name}</td>
                <td className="px-3 py-2 font-mono text-xs">{lead.mobile_number}</td>
                <td className="px-3 py-2 text-xs text-gray-500">{lead.stage_assigned}</td>
                <td className="px-3 py-2">
                  <EditableCell
                    value={lead.current_stage}
                    onSave={(v) => handleSave(lead.id, 'current_stage', v)}
                  />
                </td>
                <td className="px-3 py-2">
                  <EditableCell
                    value={lead.sub_disposition}
                    onSave={(v) => handleSave(lead.id, 'sub_disposition', v)}
                  />
                </td>
                <td className="px-3 py-2">
                  <FollowUpBadge date={lead.follow_up_date} status={lead.follow_up_status} />
                  <EditableCell
                    value={lead.follow_up_date}
                    onSave={(v) => handleSave(lead.id, 'follow_up_date', v)}
                    type="date"
                  />
                </td>
                <td className="px-3 py-2 min-w-[200px]">
                  <EditableCell
                    value={lead.remark}
                    onSave={(v) => handleSave(lead.id, 'remark', v)}
                  />
                </td>
                <td className="px-3 py-2 text-xs text-gray-500">{lead.assigned_fos_name}</td>
                <td className="px-3 py-2 text-xs text-gray-500">{lead.date_of_assignment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pages={pages} total={total} size={size} onChange={onPageChange} />

      <BulkActionBar
        selectedIds={[...selected]}
        onDone={() => { setSelected(new Set()); refetch?.() }}
      />
    </div>
  )
}
