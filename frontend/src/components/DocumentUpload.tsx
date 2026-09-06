import { useState } from 'react'
import { Upload, FileText, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { uploadDocument } from '../api/documents'

interface DocumentUploadProps {
  userId: string
  onDocumentUploaded: (document: any) => void
}

export default function DocumentUpload({ userId, onDocumentUploaded }: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file, userId),
    onSuccess: (data) => {
      onDocumentUploaded(data)
      setSelectedFile(null)
    },
  })

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === 'application/pdf') {
        setSelectedFile(file)
      } else {
        alert('Please upload a PDF file')
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  return (
    <div className="space-y-4">
      {/* Drag and Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
          dragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 bg-white hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploadMutation.isPending}
        />
        
        <div className="text-center">
          <Upload className="mx-auto w-12 h-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            <span className="font-medium text-primary-600">Click to upload</span> or drag and drop
          </p>
          <p className="mt-1 text-xs text-gray-500">PDF files only, max 100MB</p>
        </div>
      </div>

      {/* Selected File */}
      {selectedFile && (
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-primary-600" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          {!uploadMutation.isPending && (
            <button
              onClick={() => setSelectedFile(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <XCircle className="w-5 h-5" />
            </button>
          )}
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploadMutation.isPending}
        className="btn-primary w-full flex items-center justify-center space-x-2"
      >
        {uploadMutation.isPending ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing...</span>
          </>
        ) : uploadMutation.isSuccess ? (
          <>
            <CheckCircle className="w-4 h-4" />
            <span>Uploaded Successfully</span>
          </>
        ) : (
          <>
            <Upload className="w-4 h-4" />
            <span>Upload & Process</span>
          </>
        )}
      </button>

      {/* Status Messages */}
      {uploadMutation.isError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            Upload failed. Please try again.
          </p>
        </div>
      )}

      {uploadMutation.isSuccess && uploadMutation.data && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">
            Processed {uploadMutation.data.total_pages} pages successfully!
          </p>
        </div>
      )}
    </div>
  )
}
