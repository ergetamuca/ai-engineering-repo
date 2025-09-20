# Document AI Assistant

A powerful legal discovery AI assistant that allows you to upload and analyze PDF documents and CSV files using advanced AI technology.

## 🚀 Live Application

**URL**: `https://the-ai-engineer-challenge-q7oovo56g-ergetamucas-projects.vercel.app`

## ✨ Features

- **📄 PDF Analysis**: Upload and chat with PDF documents
- **📊 CSV Processing**: Upload and analyze CSV files for legal discovery
- **🤖 AI-Powered Chat**: Intelligent document analysis using OpenAI
- **⚖️ Legal Focus**: Specialized for legal discovery and document analysis
- **📱 Modern UI**: Clean, professional interface with drag-and-drop upload
- **🔄 Real-time Streaming**: Live AI responses as you chat

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **OpenAI API**: GPT-4 for document analysis and chat
- **pypdf**: PDF text extraction
- **Python CSV**: Built-in CSV processing
- **Vercel**: Serverless deployment

### Frontend
- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API calls
- **Lucide React**: Beautiful icons
- **CSS3**: Modern styling with gradients and animations

## 📁 Project Structure

```
ai-engineering-repo/
├── api/
│   ├── index.py              # Main FastAPI application
│   ├── requirements.txt      # Python dependencies
│   └── README.md            # API documentation
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx         # React entry point
│   │   └── index.css        # Global styles
│   ├── index.html           # HTML template
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite configuration
├── docs/
│   └── GIT_SETUP.md         # Git setup guide
├── .cursor/
│   └── rules/               # Cursor AI rules
├── vercel.json              # Vercel deployment config
├── MERGE.md                 # Merge instructions
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-engineering-repo
   ```

2. **Set up the backend**
   ```bash
   cd api
   pip install -r requirements.txt
   uvicorn index:app --reload
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open your browser**
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`

### Deployment

The application is deployed on Vercel and automatically updates when you push to the main branch.

## 📖 Usage

1. **Enter your OpenAI API key** in the input field
2. **Upload a document**:
   - Drag and drop a PDF or CSV file
   - Or click to browse and select
3. **Chat with your document**:
   - Ask questions about the content
   - Get AI-powered analysis and insights
   - Receive real-time streaming responses

## 🔧 API Endpoints

- `GET /api/health` - Health check
- `GET /api/document-status` - Check if documents are uploaded
- `POST /api/upload-document` - Upload PDF or CSV files
- `POST /api/rag-chat` - Chat with uploaded documents

## 📋 File Support

- **PDFs**: Up to 4MB
- **CSV files**: Up to 10MB
- **Supported formats**: PDF, CSV

## 🎯 Legal Discovery Features

- **Document Analysis**: Automatic extraction of case numbers, dates, and legal terms
- **Evidence Tracking**: Cross-reference documents and citations
- **Pattern Recognition**: Identify relationships and inconsistencies
- **Structured Data Processing**: Analyze CSV files for legal relevance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Deployed on [Vercel](https://vercel.com/)
- Powered by [OpenAI](https://openai.com/)
- Icons by [Lucide](https://lucide.dev/)

---

**Built with ❤️ for legal professionals and document analysis**