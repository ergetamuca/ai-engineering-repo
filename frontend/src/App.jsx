import React, { useState, useRef, useEffect } from 'react'
import { Upload, FileText, MessageCircle, Send, Loader, BookOpen, FileSpreadsheet } from 'lucide-react'
import axios from 'axios'

function App() {
  const [apiKey, setApiKey] = useState('')
  const [documentFile, setDocumentFile] = useState(null)
  const [documentStatus, setDocumentStatus] = useState({ hasDocuments: false, message: '', documentCount: 0, documents: [] })
  const [messages, setMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isChatting, setIsChatting] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  // Removed analysisType and chatMode - using only general chat
  
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize with empty document status (no persistence on refresh)
  useEffect(() => {
    setDocumentStatus({ hasDocuments: false, message: '', documentCount: 0, documents: [] })
  }, [])

  const handleFileSelect = (file) => {
    const fileExtension = file.name.toLowerCase().split('.').pop()
    const allowedTypes = ['pdf', 'csv']
    
    if (file && allowedTypes.includes(fileExtension)) {
      // Check file size (10MB for CSV, 4MB for PDFs)
      const MAX_FILE_SIZE = fileExtension === 'pdf' ? 4 * 1024 * 1024 : 10 * 1024 * 1024
      if (file.size > MAX_FILE_SIZE) {
        alert(`File too large. Maximum size is ${MAX_FILE_SIZE / (1024*1024)}MB. Your file is ${(file.size / (1024*1024)).toFixed(1)}MB`)
        return
      }
      setDocumentFile(file)
    } else {
      alert('Please select a PDF or CSV file')
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    handleFileSelect(file)
  }

  const handleFileInputChange = (e) => {
    const file = e.target.files[0]
    handleFileSelect(file)
  }

  const handleUpload = async () => {
    if (!documentFile || !apiKey) {
      alert('Please select a document file and enter your OpenAI API key')
      return
    }

    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', documentFile)
    formData.append('api_key', apiKey)

    try {
      const response = await axios.post('/api/upload-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        setDocumentStatus({
          hasDocuments: true,
          message: response.data.message,
          documentCount: 1, // Always 1 since we're replacing documents on each upload
          documents: [{
            id: response.data.document_id,
            filename: response.data.document_name,
            type: response.data.document_type,
            case_numbers: response.data.analysis?.case_numbers || [],
            dates: response.data.analysis?.dates || []
          }]
        })
        setMessages([]) // Clear previous messages
        alert(`Document uploaded and processed successfully! Found ${response.data.analysis?.case_numbers?.length || 0} case numbers and ${response.data.analysis?.dates?.length || 0} dates.`)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || !apiKey) {
      return
    }

    const userMessage = currentMessage.trim()
    setCurrentMessage('')
    
    // Add user message to chat
    setMessages(prev => [...prev, { 
      type: 'user', 
      content: userMessage,
      timestamp: new Date()
    }])

    // Add loading message
    setMessages(prev => [...prev, { 
      type: 'assistant', 
      content: 'Analyzing documents...',
      isLoading: true,
      timestamp: new Date()
    }])

    setIsChatting(true)

    try {
      // Use general RAG chat endpoint
      const endpoint = '/api/rag-chat'
      const requestBody = {
        user_message: userMessage,
        api_key: apiKey
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Remove loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading))

      // Stream the response
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        assistantMessage += chunk

        // Update the last message with streaming content
        setMessages(prev => {
          const newMessages = [...prev]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.type === 'assistant') {
            lastMessage.content = assistantMessage
            lastMessage.isLoading = false
          } else {
            newMessages.push({
              type: 'assistant',
              content: assistantMessage,
              isLoading: false,
              timestamp: new Date()
            })
          }
          return newMessages
        })
      }

    } catch (error) {
      console.error('Chat error:', error)
      
      // Remove loading message and add error message
      setMessages(prev => {
        const newMessages = prev.filter(msg => !msg.isLoading)
        newMessages.push({
          type: 'assistant',
          content: `Error: ${error.message}`,
          isError: true,
          timestamp: new Date()
        })
        return newMessages
      })
    } finally {
      setIsChatting(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="container">
      <div className="header">
        <div className="header-content">
          <div className="header-icon">
            <BookOpen size={48} />
          </div>
          <div className="header-text">
            <h1>Document AI Assistant</h1>
            <p>Upload documents and CSV files for intelligent analysis and chat</p>
          </div>
        </div>
        <div className="header-features">
          <div className="feature-tag">
            <FileText size={16} />
            <span>PDF Analysis</span>
          </div>
          <div className="feature-tag">
            <FileSpreadsheet size={16} />
            <span>CSV Processing</span>
          </div>
          <div className="feature-tag">
            <MessageCircle size={16} />
            <span>AI Chat</span>
          </div>
        </div>
      </div>

      <div className="content">
        {/* API Key Section */}
        <div className="api-key-section">
          <label className="api-key-label">OpenAI API Key</label>
          <input
            type="password"
            className="api-key-input"
            placeholder="Enter your OpenAI API key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>

        {/* Document Upload Section */}
        {!documentStatus.hasDocuments && (
          <div className="upload-section">
            <div
              className={`upload-area ${isDragging ? 'dragover' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="upload-icons">
                <FileText size={32} />
                <FileSpreadsheet size={32} />
              </div>
              <div className="upload-text">
                {documentFile ? documentFile.name : 'Click to upload or drag and drop'}
              </div>
              <div className="upload-subtext">
                PDFs (max 4MB) or CSV files (max 10MB)
              </div>
              <div className="supported-formats">
                Supported: PDF, CSV
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.csv"
                onChange={handleFileInputChange}
                className="file-input"
              />
            </div>
            
            <button
              className="upload-button"
              onClick={handleUpload}
              disabled={!documentFile || !apiKey || isUploading}
            >
              {isUploading ? (
                <>
                  <Loader className="loading-spinner" />
                  Processing Document...
                </>
              ) : (
                <>
                  <BookOpen size={20} style={{ marginRight: '8px' }} />
                  Upload & Analyze Document
                </>
              )}
            </button>
          </div>
        )}

        {/* Document Status */}
        {documentStatus.message && (
          <div className={`document-status ${documentStatus.hasDocuments ? 'success' : 'error'}`}>
            <div className="status-header">
              <BookOpen size={20} />
              <span>{documentStatus.message}</span>
            </div>
            {documentStatus.documents && documentStatus.documents.length > 0 && (
              <div className="document-list">
                {documentStatus.documents.map((doc, index) => (
                  <div key={doc.id || index} className="document-item">
                    <div className="document-info">
                      <div className="document-type">
                        {doc.type === 'pdf' ? <FileText size={16} /> : <FileSpreadsheet size={16} />}
                        <span>{doc.filename}</span>
                      </div>
                      {doc.case_numbers.length > 0 && (
                        <div className="case-numbers">
                          <strong>Case Numbers:</strong> {doc.case_numbers.join(', ')}
                        </div>
                      )}
                      {doc.dates.length > 0 && (
                        <div className="dates">
                          <strong>Dates:</strong> {doc.dates.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div className="document-note">
                  <small>💡 Uploading a new document will replace the current one</small>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Chat Mode Controls - Removed Legal Analysis tab */}

        {/* Chat Section */}
        {documentStatus.hasDocuments && (
          <div className="chat-section">
            <div className="chat-messages">
              {messages.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  color: '#718096', 
                  padding: '40px 20px',
                  fontStyle: 'italic'
                }}>
                  <MessageCircle size={48} style={{ marginBottom: '20px', opacity: 0.5 }} />
                  <div>Start chatting with your documents!</div>
                  <div style={{ fontSize: '0.9rem', marginTop: '10px' }}>
                    Ask questions about the content of your uploaded documents.
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`message ${message.type} ${message.isLoading ? 'loading' : ''}`}>
                    {message.content}
                    {message.isLoading && <Loader className="loading-spinner" />}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-section">
              <input
                type="text"
                className="chat-input"
                placeholder="Ask a question about your documents..."
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isChatting}
              />
              <button
                className="send-button"
                onClick={handleSendMessage}
                disabled={!currentMessage.trim() || isChatting}
              >
                {isChatting ? (
                  <Loader className="loading-spinner" />
                ) : (
                  <Send size={20} />
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
