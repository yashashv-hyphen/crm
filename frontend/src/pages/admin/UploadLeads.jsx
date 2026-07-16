import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listActivities } from '../../api/activities'
import { uploadTemplate1, uploadRegular, uploadCalls, getUploadStatus, getUploadErrors } from '../../api/uploads'
import { uploadPleLaunches, uploadPleMcidDetail } from '../../api/ple'
import toast from 'react-hot-toast'

function UploadStatus({ uploadId }) {
  const [status, setStatus] = useState({ status: 'processing' })
  const [errors, setErrors] = useState([])
  const [polling, setPolling] = useState(true)

  useEffect(() => {
    if (!polling) return
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
            ? `Upload complete — ${data.success_rows} rows updated`
            : 'Upload failed'
        )
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [uploadId, polling])

  return (
    <div className={`rounded-xl border p-5 space-y-2 ${status.status === 'completed' ? 'bg-green-50 border-green-200' : status.status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'}`}>
      <div className="font-medium text-sm">Status: <span className="uppercase">{status.status}</span></div>
      {status.total_rows != null && (
        <div className="text-sm space-y-1">
          <div>✅ {status.success_rows} rows processed successfully</div>
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
  )
}

function LeadUploadSection({ activities }) {
  const [file, setFile] = useState(null)
  const [uploadType, setUploadType] = useState('')
  const [uploadId, setUploadId] = useState(null)
  const [uploading, setUploading] = useState(false)

  const handleUpload = async () => {
    if (!file || !uploadType) { toast.error('Select a file and lead type'); return }
    try {
      setUploading(true)
      let data
      if (uploadType === 'regular') {
        const resp = await uploadRegular(file)
        data = resp.data
      } else {
        const gsiActivity = activities.find((a) => a.name === 'GSI')
        if (!gsiActivity) { toast.error('GSI activity not found in system'); return }
        const resp = await uploadTemplate1(file, gsiActivity.id)
        data = resp.data
      }
      setUploadId(data.upload_id ?? data.task_id)
      toast.success('Upload started — processing in background')
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(', ')
        : (typeof detail === 'string' ? detail : 'Upload failed')
      toast.error(msg)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Upload Leads</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Lead Type</label>
          <div className="flex gap-3">
            {[{ value: 'regular', label: 'Regular' }, { value: 'gsi', label: 'GSI' }].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setUploadType(opt.value)}
                className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                  uploadType === opt.value
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Excel File (.xlsx)</label>
          <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-gray-50 file:hover:bg-gray-100" />
          <p className="text-xs text-gray-400 mt-1">Max 5,000 rows. Do not close browser during upload.</p>
        </div>
        <button onClick={handleUpload} disabled={!file || !uploadType || uploading}
          className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
          {uploading ? 'Uploading...' : 'Upload File'}
        </button>
      </div>
      {uploadId && <UploadStatus key={uploadId} uploadId={uploadId} />}
    </div>
  )
}

function CallUploadSection() {
  const [file, setFile] = useState(null)
  const [uploadId, setUploadId] = useState(null)
  const [uploading, setUploading] = useState(false)

  const handleUpload = async () => {
    if (!file) { toast.error('Select a file'); return }
    try {
      setUploading(true)
      const { data } = await uploadCalls(file)
      setUploadId(data.upload_id ?? data.task_id)
      toast.success('Call update started — processing in background')
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg).join(', ')
        : (typeof detail === 'string' ? detail : 'Upload failed')
      toast.error(msg)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Upload Call Update</h2>
          <p className="text-xs text-gray-400 mt-0.5">Expects call log file with <span className="font-mono">MCID</span> and <span className="font-mono">Call time (In min)</span> columns. Aggregates by MCID automatically.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Excel File (.xlsx)</label>
          <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-gray-50 file:hover:bg-gray-100" />
        </div>
        <button onClick={handleUpload} disabled={!file || uploading}
          className="w-full bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
          {uploading ? 'Uploading...' : 'Upload Call Data'}
        </button>
      </div>
      {uploadId && <UploadStatus key={uploadId} uploadId={uploadId} />}
    </div>
  )
}

function PleUploadSection() {
  const [launchesFile, setLaunchesFile] = useState(null)
  const [mcidFile, setMcidFile] = useState(null)
  const [launchesUploadId, setLaunchesUploadId] = useState(null)
  const [mcidUploadId, setMcidUploadId] = useState(null)
  const [uploadingLaunches, setUploadingLaunches] = useState(false)
  const [uploadingMcid, setUploadingMcid] = useState(false)

  const handleError = (err) => {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(', ')
      : (typeof detail === 'string' ? detail : 'Upload failed')
    toast.error(msg)
  }

  const handleUploadLaunches = async () => {
    if (!launchesFile) { toast.error('Select a file'); return }
    try {
      setUploadingLaunches(true)
      const { data } = await uploadPleLaunches(launchesFile)
      setLaunchesUploadId(data.upload_id ?? data.task_id)
      toast.success('PLE launches upload started — processing in background')
    } catch (err) {
      handleError(err)
    } finally {
      setUploadingLaunches(false)
    }
  }

  const handleUploadMcid = async () => {
    if (!mcidFile) { toast.error('Select a file'); return }
    try {
      setUploadingMcid(true)
      const { data } = await uploadPleMcidDetail(mcidFile)
      setMcidUploadId(data.upload_id ?? data.task_id)
      toast.success('PLE working file upload started — processing in background')
    } catch (err) {
      handleError(err)
    } finally {
      setUploadingMcid(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Upload PLE Launches File</h2>
          <p className="text-xs text-gray-400 mt-0.5">The weekly launches workbook (.xlsb) — feeds the PLE tab's user-wise breakdown.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select File (.xlsb)</label>
          <input type="file" accept=".xlsb" onChange={(e) => setLaunchesFile(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-gray-50 file:hover:bg-gray-100" />
        </div>
        <button onClick={handleUploadLaunches} disabled={!launchesFile || uploadingLaunches}
          className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
          {uploadingLaunches ? 'Uploading...' : 'Upload Launches File'}
        </button>
      </div>
      {launchesUploadId && <UploadStatus key={launchesUploadId} uploadId={launchesUploadId} />}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Upload PLE Working File</h2>
          <p className="text-xs text-gray-400 mt-0.5">The weekly per-MCID working sheet (.xlsx) — feeds the PLE tab's MCID-wise breakdown.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select File (.xlsx)</label>
          <input type="file" accept=".xlsx" onChange={(e) => setMcidFile(e.target.files[0])}
            className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-gray-50 file:hover:bg-gray-100" />
        </div>
        <button onClick={handleUploadMcid} disabled={!mcidFile || uploadingMcid}
          className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
          {uploadingMcid ? 'Uploading...' : 'Upload Working File'}
        </button>
      </div>
      {mcidUploadId && <UploadStatus key={mcidUploadId} uploadId={mcidUploadId} />}
    </div>
  )
}

export default function UploadLeads() {
  const { data: activities = [] } = useQuery({
    queryKey: ['activities'],
    queryFn: () => listActivities().then((r) => r.data),
  })

  return (
    <div className="space-y-8 max-w-2xl">
      <h1 className="text-xl font-bold text-gray-800">Uploads</h1>
      <LeadUploadSection activities={activities} />
      <CallUploadSection />
      <PleUploadSection />
    </div>
  )
}
