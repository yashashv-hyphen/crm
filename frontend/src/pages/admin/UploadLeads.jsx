import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listActivities } from '../../api/activities'
import { uploadTemplate1, getUploadStatus, getUploadErrors } from '../../api/uploads'
import toast from 'react-hot-toast'
import api from '../../api/axios'

export default function UploadLeads() {
  const [file, setFile] = useState(null)
  const [activityId, setActivityId] = useState('')
  const [uploadId, setUploadId] = useState(null)
  const [status, setStatus] = useState(null)
  const [errors, setErrors] = useState([])
  const [polling, setPolling] = useState(false)

  const { data: activities = [] } = useQuery({
    queryKey: ['activities'],
    queryFn: () => listActivities().then((r) => r.data),
  })

  useEffect(() => {
    if (!uploadId || !polling) return
    const interval = setInterval(async () => {
      const { data } = await getUploadStatus(uploadId)
      setStatus(data)
      if (data.status === 'completed' || data.status === 'failed') {
        setPolling(false)
        clearInterval(interval)
        if (data.error_rows > 0) {
          const errResp = await getUploadErrors(uploadId)
          setErrors(errResp.data.errors)
        }
        toast[data.status === 'completed' ? 'success' : 'error'](
          data.status === 'completed' ? `Upload complete — ${data.success_rows} leads added` : 'Upload failed'
        )
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [uploadId, polling])

  const handleUpload = async () => {
    if (!file || !activityId) { toast.error('Select a file and activity'); return }
    try {
      const { data } = await uploadTemplate1(file, activityId)
      setUploadId(data.upload_id)
      setPolling(true)
      setStatus({ status: 'processing' })
      setErrors([])
      toast.success('Upload started — processing in background')
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(', ')
        : (typeof detail === 'string' ? detail : 'Upload failed')
      toast.error(msg)
    }
  }

  const downloadTemplate = () => {
    window.open('/api/templates/template1', '_blank')
  }

  const downloadErrors = () => {
    // Build error Excel download from uploadId
    window.open(`/api/uploads/${uploadId}/errors?format=excel`, '_blank')
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Upload Leads (Template 1)</h1>
        <button onClick={downloadTemplate} className="text-sm text-blue-600 hover:underline">
          Download Template 1
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Activity</label>
          <select
            value={activityId}
            onChange={(e) => setActivityId(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">— Select activity —</option>
            {activities.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Excel File (.xlsx)</label>
          <input
            type="file"
            accept=".xlsx"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-gray-50 file:hover:bg-gray-100"
          />
          <p className="text-xs text-gray-400 mt-1">Max 5,000 rows. Do not close browser during upload.</p>
        </div>
        <button
          onClick={handleUpload}
          disabled={!file || !activityId || polling}
          className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {polling ? 'Processing...' : 'Upload File'}
        </button>
      </div>

      {status && (
        <div className={`rounded-xl border p-5 space-y-2 ${status.status === 'completed' ? 'bg-green-50 border-green-200' : status.status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'}`}>
          <div className="font-medium text-sm">
            Status: <span className="uppercase">{status.status}</span>
          </div>
          {status.total_rows != null && (
            <div className="text-sm space-y-1">
              <div>✅ {status.success_rows} leads uploaded successfully</div>
              {status.error_rows > 0 && <div>❌ {status.error_rows} rows had errors</div>}
            </div>
          )}
          {errors.length > 0 && (
            <div className="mt-3">
              <div className="font-medium text-sm text-red-700 mb-2">Error Report ({errors.length} rows):</div>
              <div className="bg-white rounded border border-red-200 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-red-50 text-gray-500">
                    <tr>
                      <th className="px-3 py-2 text-left">Row</th>
                      <th className="px-3 py-2 text-left">Merchant ID</th>
                      <th className="px-3 py-2 text-left">Error</th>
                      <th className="px-3 py-2 text-left">Detail</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-50">
                    {errors.slice(0, 20).map((e, i) => (
                      <tr key={i}>
                        <td className="px-3 py-1.5">{e.row_number}</td>
                        <td className="px-3 py-1.5 font-mono">{e.merchant_id || '—'}</td>
                        <td className="px-3 py-1.5 text-red-600">{e.error_type}</td>
                        <td className="px-3 py-1.5 text-gray-600">{e.error_detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
