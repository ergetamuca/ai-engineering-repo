# PDF RAG Chat Frontend

A modern React application for chatting with PDF documents using AI-powered RAG (Retrieval-Augmented Generation).

## Features

- **PDF Upload**: Drag-and-drop or click to upload PDF files
- **Real-time Chat**: Stream responses from AI based on PDF content
- **Modern UI**: Beautiful, responsive design with gradient backgrounds
- **API Key Management**: Secure OpenAI API key input
- **Status Indicators**: Real-time feedback on PDF processing and chat status

## Prerequisites

- Node.js 16+ and npm
- OpenAI API key
- Backend API running on port 8000

## Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Usage

1. **Enter API Key**: Input your OpenAI API key in the provided field
2. **Upload PDF**: Drag and drop a PDF file or click to select one
3. **Wait for Processing**: The system will extract text and create embeddings
4. **Start Chatting**: Ask questions about your PDF content
5. **Get AI Responses**: Receive context-aware answers based on your PDF

## Technical Details

- **Framework**: React 18 with Vite
- **Styling**: Custom CSS with modern gradients and animations
- **HTTP Client**: Axios for API communication
- **Icons**: Lucide React for consistent iconography
- **State Management**: React hooks for local state
- **Streaming**: Real-time message streaming from backend

## API Integration

The frontend communicates with the backend through these endpoints:
- `POST /api/upload-pdf` - Upload and process PDF
- `POST /api/rag-chat` - Chat with processed PDF
- `GET /api/pdf-status` - Check PDF processing status

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your OpenAI API key is valid and has sufficient credits
2. **PDF Upload Fails**: Check that the file is a valid PDF and under 10MB
3. **Chat Not Working**: Verify the backend is running and PDF was processed successfully
4. **CORS Issues**: Ensure the backend CORS settings allow requests from localhost:3000

### Development Tips

- Use browser dev tools to inspect network requests
- Check the console for error messages
- Verify API responses in the Network tab
- Test with different PDF files to ensure compatibility