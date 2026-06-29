import { useState, useEffect } from 'react'
import { uploadTemplate2, getUploadStatus, getUploadErrors } from '../../api/uploads'
import toast from 'react-hot-toast'

export default function UploadFinalStage() {
  const [file, setFile] = useState(null)
  const [uploadId, setUploadId] = useState(null)
  const [status, setStatus] = useState(null)
  const [errors, setErrors] = useState([])
  const [polling, setPolling] = useState(false)

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
          data.status === 'completed'
            ? `Final stage update complete — ${data.success_rows} leads moved`
            : 'Upload failed'
        )
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [uploadId, polling])

  const handleUpload = async () => {
    if (!file) { toast.error('Select a file'); return }
    try {
      const { data } = await uploadTemplate2(file)
      setUploadId(data.upload_id)
      setPolling(true)
      setStatus({ status: 'processing' })
      setErrors([])
      toast.success('Upload started — leads will move to next stage automatically')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Upload Final Stage (Template 2)</h1>
        <a href="/api/templates/template2" target="_blank" className="text-sm text-blue-600 hover:underline">
          Download Template 2
        </a>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        This upload will trigger lead movement to the next activity. Leads with a matching Final Stage will move automatically.
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Template 2 File (.xlsx)</label>
          <input
            type="file"
            accept=".xlsx"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-gray-50 file:hover:bg-gray-100"
          />
        </div>
        <button
          onClick={handleUpload}
          disabled={!file || polling}
          className="w-full bg-amber-600 text-white py-2 rounded-lg text-sm hover:bg-amber-700 disabled:opacity-50"
        >
          {polling ? 'Processing...' : 'Upload & Move Leads'}
        </button>
      </div>

      {status && (
        <div className={`rounded-xl border p-5 space-y-2 ${status.status === 'completed' ? 'bg-green-50 border-green-200' : status.status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'}`}>
          <div className="font-medium text-sm">Status: <span className="uppercase">{status.status}</span></div>
          {status.total_rows != null && (
            <div className="text-sm space-y-1">
              <div>✅ {status.success_rows} leads updated/moved</div>
              {status.error_rows > 0 && <div>❌ {status.error_rows} rows had errors</div>}
            </div>
          )}
          {errors.length > 0 && (
            <div className="mt-3 text-xs">
              <div className="font-medium text-red-700 mb-2">Errors ({errors.length}):</div>
              {errors.slice(0, 10).map((e, i) => (
                <div key={i} className="text-gray-600">Row {e.row_number}: {e.error_type} — {e.error_detail}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
