import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getLead, updateLead, getLeadHistory } from '../api/leads'
import AgingFlag from './AgingFlag'
import FollowUpBadge from './FollowUpBadge'
import toast from 'react-hot-toast'

function DetailRow({ label, value }) {
  if (!value && value !== 0) return null
  return (
    <div className="flex gap-2 py-1.5 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500 w-36 shrink-0">{label}</span>
      <span className="text-xs text-gray-800 font-medium break-all">{value}</span>
    </div>
  )
}

function EntryDates({ lead }) {
  const dates = [
    { label: 'RNC', value: lead.rnc_entry_date },
    { label: 'IDV', value: lead.idv_entry_date },
    { label: 'RTL', value: lead.rtl_entry_date },
    { label: 'FBA', value: lead.fba_entry_date },
    { label: 'SP', value: lead.sp_entry_date },
    { label: 'Open Spending', value: lead.open_spending_entry_date },
    { label: 'NARF', value: lead.narf_entry_date },
    { label: 'GSI', value: lead.gsi_entry_date },
  ].filter((d) => d.value)

  if (!dates.length) return null
  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Stage Entry Dates</p>
      <div className="grid grid-cols-2 gap-x-4">
        {dates.map((d) => (
          <div key={d.label} className="flex gap-1 py-1 border-b border-gray-50 text-xs">
            <span className="text-gray-500 w-24 shrink-0">{d.label}</span>
            <span className="text-gray-800 font-medium">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function HistoryTab({ leadId }) {
  const { data: history, isLoading } = useQuery({
    queryKey: ['lead-history', leadId],
    queryFn: () => getLeadHistory(leadId).then((r) => r.data),
  })

  if (isLoading) return <p className="text-sm text-gray-400 py-4 text-center">Loading history…</p>
  if (!history?.length) return <p className="text-sm text-gray-400 py-4 text-center">No changes recorded yet.</p>

  return (
    <div className="space-y-2 mt-2">
      {history.map((entry, i) => (
        <div key={i} className="bg-gray-50 rounded-lg px-3 py-2 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-gray-700">{entry.action_type}</span>
            <span className="text-gray-400">{new Date(entry.performed_at).toLocaleString()}</span>
          </div>
          <div className="text-gray-500">
            {entry.performed_by_name && <span className="font-medium text-gray-600">{entry.performed_by_name} · </span>}
            {entry.old_value != null && (
              <span><span className="line-through text-red-400">{entry.old_value}</span> → </span>
            )}
            <span className="text-green-700 font-medium">{entry.new_value ?? '—'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function LeadDetailDrawer({ lead: initialLead, onClose, onSaved }) {
  const [tab, setTab] = useState('details')
  const [form, setForm] = useState({
    current_stage: '',
    sub_disposition: '',
    remark: '',
    follow_up_date: '',
    alternate_phone: '',
    alternate_phone_2: '',
  })
  const queryClient = useQueryClient()

  const { data: lead } = useQuery({
    queryKey: ['lead', initialLead.id],
    queryFn: () => getLead(initialLead.id).then((r) => r.data),
    initialData: initialLead,
    staleTime: 30_000,
  })

  useEffect(() => {
    if (lead) {
      setForm({
        current_stage: lead.current_stage || '',
        sub_disposition: lead.sub_disposition || '',
        remark: lead.remark || '',
        follow_up_date: lead.follow_up_date || '',
        alternate_phone: lead.alternate_phone || '',
        alternate_phone_2: lead.alternate_phone_2 || '',
      })
    }
  }, [lead?.id])

  const mutation = useMutation({
    mutationFn: (updates) => updateLead(lead.id, updates),
    onSuccess: (res) => {
      queryClient.setQueryData(['lead', lead.id], res.data)
      toast.success('Saved')
      onSaved?.()
    },
    onError: () => toast.error('Save failed'),
  })

  const handleSave = () => {
    const updates = {}
    if (form.current_stage !== (lead.current_stage || '')) updates.current_stage = form.current_stage || null
    if (form.sub_disposition !== (lead.sub_disposition || '')) updates.sub_disposition = form.sub_disposition || null
    if (form.remark !== (lead.remark || '')) updates.remark = form.remark || null
    if (form.follow_up_date !== (lead.follow_up_date || '')) updates.follow_up_date = form.follow_up_date || null
    if (form.alternate_phone !== (lead.alternate_phone || '')) updates.alternate_phone = form.alternate_phone || null
    if (form.alternate_phone_2 !== (lead.alternate_phone_2 || '')) updates.alternate_phone_2 = form.alternate_phone_2 || null
    if (!Object.keys(updates).length) { toast('No changes to save', { icon: 'ℹ️' }); return }
    mutation.mutate(updates)
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Overlay */}
      <div className="flex-1 bg-black/30" onClick={onClose} />

      {/* Drawer panel */}
      <div className="w-full max-w-lg bg-white shadow-2xl flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
          <div>
            <p className="text-xs text-gray-500">Merchant ID</p>
            <p className="font-mono text-sm font-bold text-gray-800">{lead.merchant_id}</p>
          </div>
          <div className="flex items-center gap-2">
            {lead.is_self_created && (
              <span className="bg-green-100 text-green-700 text-xs font-semibold px-2 py-0.5 rounded-full">New Registration</span>
            )}
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-100 shrink-0">
          {['details', 'update', 'history'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2.5 text-sm font-medium capitalize transition-colors ${
                tab === t
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {tab === 'details' && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Lead Information</p>
              <DetailRow label="Seller Name" value={lead.seller_name} />
              <DetailRow label="Mobile Number" value={lead.mobile_number} />
              <DetailRow label="Alternate Phone" value={lead.alternate_phone} />
              <DetailRow label="Alternate Phone 2" value={lead.alternate_phone_2} />
              <DetailRow label="Email" value={lead.email_id} />
              <DetailRow label="Stage Assigned" value={lead.stage_assigned} />
              <DetailRow label="Assignment Date" value={lead.date_of_assignment} />
              <DetailRow
                label="Week / Year"
                value={(() => {
                  const wk = lead.week_no ?? (() => {
                    if (!lead.date_of_assignment) return null
                    const d = new Date(lead.date_of_assignment)
                    const jan4 = new Date(d.getFullYear(), 0, 4)
                    const startOfWeek1 = new Date(jan4)
                    startOfWeek1.setDate(jan4.getDate() - jan4.getDay() + 1)
                    return Math.ceil(((d - startOfWeek1) / 86400000 + 1) / 7)
                  })()
                  const yr = lead.year ?? (lead.date_of_assignment ? new Date(lead.date_of_assignment).getFullYear() : null)
                  return wk ? `Week ${wk}, ${yr}` : null
                })()}
              />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Stage Status</p>
              <DetailRow label="Current Stage" value={lead.current_stage} />
              <DetailRow label="Sub-Disposition" value={lead.sub_disposition} />
              <DetailRow label="Final Stage" value={lead.final_stage} />
              <div className="flex gap-2 py-1.5 border-b border-gray-50">
                <span className="text-xs text-gray-500 w-36 shrink-0">Aging</span>
                <div className="flex items-center gap-2">
                  <AgingFlag color={lead.aging_color} />
                  {lead.aging_days != null && (
                    <span className="text-xs text-gray-700">{lead.aging_days} days</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 py-1.5 border-b border-gray-50">
                <span className="text-xs text-gray-500 w-36 shrink-0">Follow-up</span>
                <div className="flex items-center gap-2">
                  <FollowUpBadge date={lead.follow_up_date} status={lead.follow_up_status} />
                  {lead.follow_up_date && (
                    <span className="text-xs text-gray-700">{lead.follow_up_date}</span>
                  )}
                </div>
              </div>

              {(lead.call_count > 0 || lead.total_call_time > 0) && (
                <>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Call Activity</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-blue-50 rounded-lg px-3 py-2 text-center">
                      <div className="text-lg font-bold text-blue-700">{lead.call_count ?? 0}</div>
                      <div className="text-xs text-blue-500">Total Calls</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg px-3 py-2 text-center">
                      <div className="text-lg font-bold text-blue-700">{(+lead.total_call_time || 0).toFixed(2)} min</div>
                      <div className="text-xs text-blue-500">Total Call Time</div>
                    </div>
                  </div>
                </>
              )}

              {lead.remark && (
                <>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Remark</p>
                  <p className="text-xs text-gray-700 bg-gray-50 rounded-lg px-3 py-2">{lead.remark}</p>
                </>
              )}

              <EntryDates lead={lead} />
            </div>
          )}

          {tab === 'update' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Current Stage</label>
                <input
                  type="text"
                  value={form.current_stage}
                  onChange={(e) => setForm((f) => ({ ...f, current_stage: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. In Progress"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Sub-Disposition</label>
                <input
                  type="text"
                  value={form.sub_disposition}
                  onChange={(e) => setForm((f) => ({ ...f, sub_disposition: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Call Back"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Follow-up Date</label>
                <input
                  type="date"
                  value={form.follow_up_date}
                  onChange={(e) => setForm((f) => ({ ...f, follow_up_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Alternate Phone Number</label>
                <input
                  type="tel"
                  value={form.alternate_phone}
                  onChange={(e) => setForm((f) => ({ ...f, alternate_phone: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter alternate phone"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Alternate Phone Number 2</label>
                <input
                  type="tel"
                  value={form.alternate_phone_2}
                  onChange={(e) => setForm((f) => ({ ...f, alternate_phone_2: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter second alternate phone"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Remarks</label>
                <textarea
                  value={form.remark}
                  onChange={(e) => setForm((f) => ({ ...f, remark: e.target.value }))}
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="Add a remark…"
                />
              </div>
              <button
                onClick={handleSave}
                disabled={mutation.isPending}
                className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          )}

          {tab === 'history' && <HistoryTab leadId={lead.id} />}
        </div>
      </div>
    </div>
  )
}
