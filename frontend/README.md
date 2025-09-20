# Document AI Assistant Frontend

React frontend for the Document AI Assistant application.

## 🚀 Features

- **Modern UI**: Clean, professional interface with legal theme
- **Drag & Drop**: Easy file upload with visual feedback
- **Real-time Chat**: Streaming AI responses
- **File Validation**: Client-side size and type checking
- **Responsive Design**: Works on desktop and mobile
- **Legal Focus**: Specialized for legal document analysis

## 🛠️ Technology Stack

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API communication
- **Lucide React**: Beautiful, consistent icons
- **CSS3**: Modern styling with gradients and animations

## 📦 Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "axios": "^1.6.0",
  "lucide-react": "^0.263.1"
}
```

## 🚀 Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Open `http://localhost:5173` in your browser

### Build for Production
```bash
npm run build
```

### Vercel Build
```bash
npm run vercel-build
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── main.jsx         # React entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── vite.config.js       # Vite configuration
└── README.md           # This file
```

## 🎨 UI Components

### Header
- Application title and description
- Feature tags (PDF Analysis, CSV Processing, AI Chat)
- Professional legal theme with blue/gold colors

### Upload Section
- Drag and drop file upload
- File type validation (PDF, CSV)
- Size limit indicators
- Visual feedback for file selection

### Document Status
- Shows uploaded document information
- Displays extracted metadata (case numbers, dates)
- Document type indicators with icons

### Chat Interface
- Real-time streaming responses
- Message history
- Loading states and error handling
- Professional legal-themed styling

## 🔧 Configuration

### File Upload
- **PDF**: Maximum 4MB
- **CSV**: Maximum 10MB
- **Supported Types**: PDF, CSV
- **Validation**: Client-side and server-side

### API Integration
- Base URL: Configured for Vercel deployment
- Endpoints: `/api/upload-document`, `/api/rag-chat`, `/api/document-status`
- Error Handling: User-friendly error messages

## 🎯 Features

### Document Upload
- Drag and drop interface
- Click to browse files
- Real-time file validation
- Progress indicators

### Chat Interface
- Streaming AI responses
- Message history
- Context-aware prompts
- Legal-focused analysis

### Responsive Design
- Mobile-friendly layout
- Adaptive components
- Touch-friendly interactions
- Cross-browser compatibility

## 🚨 Error Handling

- File size validation with clear messages
- File type validation
- Network error handling
- API error display
- Graceful fallbacks

## 🎨 Styling

- **Color Scheme**: Professional blue and gold legal theme
- **Typography**: Clean, readable fonts
- **Animations**: Smooth transitions and hover effects
- **Icons**: Consistent Lucide React icons
- **Layout**: Responsive grid and flexbox

## 🔧 Development Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run vercel-build` - Build for Vercel deployment
- `npm run preview` - Preview production build

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚀 Deployment

The frontend is automatically deployed to Vercel when changes are pushed to the main branch. The build process uses Vite for optimal performance and modern JavaScript features.