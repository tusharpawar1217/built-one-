import { FileText, CheckCircle } from 'lucide-react'

interface Document {
  document_id: string
  filename: string
  total_pages: number
  status: string
}

interface DocumentListProps {
  documents: Document[]
  selectedDocuments: string[]
  onSelectionChange: (documentIds: string[]) => void
}

export default function DocumentList({
  documents,
  selectedDocuments,
  onSelectionChange,
}: DocumentListProps) {
  const toggleDocument = (documentId: string) => {
    if (selectedDocuments.includes(documentId)) {
      onSelectionChange(selectedDocuments.filter(id => id !== documentId))
    } else {
      onSelectionChange([...selectedDocuments, documentId])
    }
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-600">No documents uploaded yet</p>
        <p className="text-xs text-gray-500 mt-1">
          Upload PDFs to start asking questions
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto">
      {documents.map((doc) => (
        <button
          key={doc.document_id}
          onClick={() => toggleDocument(doc.document_id)}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            selectedDocuments.includes(doc.document_id)
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 bg-white hover:border-gray-300'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1 min-w-0">
              <FileText className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                selectedDocuments.includes(doc.document_id)
                  ? 'text-primary-600'
                  : 'text-gray-400'
              }`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {doc.filename}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {doc.total_pages} pages
                </p>
              </div>
            </div>
            {selectedDocuments.includes(doc.document_id) && (
              <CheckCircle className="w-5 h-5 text-primary-600 flex-shrink-0" />
            )}
          </div>
        </button>
      ))}
    </div>
  )
}
