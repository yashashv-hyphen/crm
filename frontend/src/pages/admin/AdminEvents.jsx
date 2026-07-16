import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getCampaigns, uploadCampaign, toggleCampaign } from '../../api/campaigns'
import toast from 'react-hot-toast'

export default function AdminEvents() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef()

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: () => getCampaigns().then((r) => r.data),
  })

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!name.trim()) { toast.error('Event name is required'); return }
    if (!file) { toast.error('Please select an Excel file'); return }
    try {
      setUploading(true)
      await uploadCampaign(name.trim(), file)
      toast.success('Event uploaded — leads are being processed')
      setName('')
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
      queryClient.invalidateQueries(['campaigns'])
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleToggle = async (id, isActive) => {
    try {
      await toggleCampaign(id)
      toast.success(isActive ? 'Event deactivated' : 'Event activated')
      queryClient.invalidateQueries(['campaigns'])
    } catch {
      toast.error('Failed to update event')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-800">Events</h1>

      {/* Upload form */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="font-semibold text-gray-700 mb-4">Create New Event</h2>
        <form onSubmit={handleUpload} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-48">
            <label className="block text-xs text-gray-500 mb-1">Event Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Q3 Reactivation Drive"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex-1 min-w-48">
            <label className="block text-xs text-gray-500 mb-1">Excel File (MCID + Remark columns)</label>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={uploading}
            className="bg-blue-600 text-white rounded-lg px-5 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {uploading ? 'Uploading…' : 'Upload Event'}
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-2">
          Excel must have an MCID column and optionally a Remark column. One row per merchant.
        </p>
      </div>

      {/* Event list */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">All Events</h2>
        </div>
        {isLoading ? (
          <p className="text-center py-8 text-gray-400 text-sm">Loading…</p>
        ) : campaigns.length === 0 ? (
          <p className="text-center py-8 text-gray-400 text-sm">No events yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-5 py-3 text-left">Event Name</th>
                <th className="px-5 py-3 text-left">Created</th>
                <th className="px-5 py-3 text-center">Status</th>
                <th className="px-5 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {campaigns.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-800">{c.name}</td>
                  <td className="px-5 py-3 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                  <td className="px-5 py-3 text-center">
                    <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${
                      c.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {c.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-center">
                    <button
                      onClick={() => handleToggle(c.id, c.is_active)}
                      className={`text-xs font-medium px-3 py-1 rounded border ${
                        c.is_active
                          ? 'border-red-300 text-red-600 hover:bg-red-50'
                          : 'border-green-300 text-green-600 hover:bg-green-50'
                      }`}
                    >
                      {c.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
