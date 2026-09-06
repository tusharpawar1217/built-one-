import { useState } from 'react'
import { FileText, MessageSquare, Upload } from 'lucide-react'
import DocumentUpload from './components/DocumentUpload'
import ChatInterface from './components/ChatInterface'
import DocumentList from './components/DocumentList'

function App() {
  const [userId] = useState('demo-user') // TODO: Replace with actual auth
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([])
  const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([])

  const handleDocumentUploaded = (document: any) => {
    setUploadedDocuments(prev => [...prev, document])
    setSelectedDocuments(prev => [...prev, document.document_id])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-600 rounded-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Sarkari AI</h1>
                <p className="text-sm text-gray-600">Your Exam Prep Assistant</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                Free Tier
              </span>
              <span className="text-sm text-gray-600">
                3/3 queries left today
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar - Document Management */}
          <div className="lg:col-span-1 space-y-6">
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <Upload className="w-5 h-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-gray-900">Upload Document</h2>
              </div>
              <DocumentUpload 
                userId={userId}
                onDocumentUploaded={handleDocumentUploaded}
              />
            </div>

            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="w-5 h-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-gray-900">My Documents</h2>
              </div>
              <DocumentList
                documents={uploadedDocuments}
                selectedDocuments={selectedDocuments}
                onSelectionChange={setSelectedDocuments}
              />
            </div>
          </div>

          {/* Right Section - Chat Interface */}
          <div className="lg:col-span-2">
            <div className="card h-[calc(100vh-180px)]">
              <div className="flex items-center space-x-2 mb-4">
                <MessageSquare className="w-5 h-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-gray-900">Ask Questions</h2>
              </div>
              <ChatInterface
                userId={userId}
                selectedDocuments={selectedDocuments}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            Sarkari AI - Preparing students for UPSC, MPSC, SSC, Banking & Railways exams
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
