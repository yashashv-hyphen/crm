import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getCampaignLeads } from '../api/campaigns'
import LeadDetailDrawer from '../components/LeadDetailDrawer'

export default function FosEvents() {
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['campaign-leads'],
    queryFn: () => getCampaignLeads().then((r) => r.data),
  })

  // Group by campaign
  const byCampaign = data.reduce((acc, item) => {
    const key = item.campaign_id
    if (!acc[key]) acc[key] = { name: item.campaign_name, leads: [] }
    acc[key].leads.push(item)
    return acc
  }, {})

  if (isLoading) return <div className="text-center py-12 text-gray-400">Loading…</div>

  if (!data.length) return (
    <div className="text-center py-20 text-gray-400">
      <div className="text-4xl mb-3">📋</div>
      <p className="text-sm">No active event leads assigned to you.</p>
    </div>
  )

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-800">Events</h1>

      {Object.entries(byCampaign).map(([cid, { name, leads }]) => (
        <div key={cid} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-700">{name}</h2>
            <span className="text-xs text-gray-400">{leads.length} lead{leads.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Merchant ID</th>
                  <th className="px-4 py-3 text-left">Seller Name</th>
                  <th className="px-4 py-3 text-left">Mobile</th>
                  <th className="px-4 py-3 text-left">Current Stage</th>
                  <th className="px-4 py-3 text-left">Event Remark</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {leads.map((item) => (
                  <tr
                    key={item.lead.id}
                    className="hover:bg-blue-50 cursor-pointer"
                    onClick={() => setSelected(item)}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">{item.lead.merchant_id}</td>
                    <td className="px-4 py-3 text-gray-800">{item.lead.seller_name || '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs">{item.lead.mobile_number || '—'}</td>
                    <td className="px-4 py-3 text-gray-600">{item.lead.current_stage || '—'}</td>
                    <td className="px-4 py-3 text-gray-500 italic">{item.event_remark || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {selected && (
        <LeadDetailDrawer
          lead={selected.lead}
          onClose={() => setSelected(null)}
          onSaved={() => {
            queryClient.invalidateQueries(['campaign-leads'])
            setSelected(null)
          }}
        />
      )}
    </div>
  )
}
