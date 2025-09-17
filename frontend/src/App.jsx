import React, { useState, useRef, useEffect } from 'react'
import { Upload, FileText, MessageCircle, Send, Loader } from 'lucide-react'
import axios from 'axios'

function App() {
  const [apiKey, setApiKey] = useState('')
  const [pdfFile, setPdfFile] = useState(null)
  const [pdfStatus, setPdfStatus] = useState({ hasPdf: false, message: '' })
  const [messages, setMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isChatting, setIsChatting] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check PDF status on component mount
  useEffect(() => {
    checkPdfStatus()
  }, [])

  const checkPdfStatus = async () => {
    try {
      const response = await axios.get('/api/pdf-status')
      setPdfStatus(response.data)
    } catch (error) {
      console.error('Error checking PDF status:', error)
    }
  }

  const handleFileSelect = (file) => {
    if (file && file.type === 'application/pdf') {
      // Check file size (4MB limit for Vercel)
      const MAX_FILE_SIZE = 4 * 1024 * 1024 // 4MB
      if (file.size > MAX_FILE_SIZE) {
        alert(`File too large. Maximum size is 4MB. Your file is ${(file.size / (1024*1024)).toFixed(1)}MB`)
        return
      }
      setPdfFile(file)
    } else {
      alert('Please select a PDF file')
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
    if (!pdfFile || !apiKey) {
      alert('Please select a PDF file and enter your OpenAI API key')
      return
    }

    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', pdfFile)
    formData.append('api_key', apiKey)

    try {
      const response = await axios.post('/api/upload-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        setPdfStatus({
          hasPdf: true,
          message: response.data.message
        })
        setMessages([]) // Clear previous messages
        alert('PDF uploaded and processed successfully!')
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
      content: 'Thinking...',
      isLoading: true,
      timestamp: new Date()
    }])

    setIsChatting(true)

    try {
      const response = await fetch('/api/rag-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_message: userMessage,
          api_key: apiKey
        }),
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
        <h1>PDF RAG Chat</h1>
        <p>Upload a PDF and chat with it using AI</p>
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

        {/* PDF Upload Section */}
        {!pdfStatus.hasPdf && (
          <div className="upload-section">
            <div
              className={`upload-area ${isDragging ? 'dragover' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="upload-icon" />
              <div className="upload-text">
                {pdfFile ? pdfFile.name : 'Click to upload or drag and drop'}
              </div>
              <div className="upload-subtext">
                PDF files only (max 4MB)
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileInputChange}
                className="file-input"
              />
            </div>
            
            <button
              className="upload-button"
              onClick={handleUpload}
              disabled={!pdfFile || !apiKey || isUploading}
            >
              {isUploading ? (
                <>
                  <Loader className="loading-spinner" />
                  Processing PDF...
                </>
              ) : (
                <>
                  <FileText size={20} style={{ marginRight: '8px' }} />
                  Upload & Process PDF
                </>
              )}
            </button>
          </div>
        )}

        {/* PDF Status */}
        {pdfStatus.message && (
          <div className={`pdf-status ${pdfStatus.hasPdf ? 'success' : 'error'}`}>
            {pdfStatus.message}
          </div>
        )}

        {/* Chat Section */}
        {pdfStatus.hasPdf && (
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
                  <div>Start chatting with your PDF!</div>
                  <div style={{ fontSize: '0.9rem', marginTop: '10px' }}>
                    Ask questions about the content of your uploaded document.
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
                placeholder="Ask a question about your PDF..."
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
