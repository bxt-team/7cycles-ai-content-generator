# Instagram Content Generator with CrewAI

A state-of-the-art content generation system using CrewAI flows to create engaging Instagram posts from knowledge files. The system generates both text content and images, with a React frontend for preview and approval.

## Features

- **Knowledge-Based Content**: Uses your knowledge files (affirmations, wellness tips) to generate authentic content
- **AI-Powered Workflow**: CrewAI flows with specialized agents for research, writing, and image creation
- **Visual Content Generation**: DALL-E 3 integration for creating stunning Instagram-ready images
- **Approval System**: React frontend to preview and approve content before publishing
- **Real-time Status Updates**: Live tracking of content generation progress

## Architecture

### CrewAI Agents
- **Researcher Agent**: Analyzes knowledge files and identifies trending topics
- **Writer Agent**: Creates compelling Instagram captions with hooks and CTAs
- **Image Creator Agent**: Generates detailed prompts for visual content

### Technology Stack
- **Backend**: FastAPI with CrewAI flows
- **Frontend**: React with TypeScript
- **AI Integration**: OpenAI GPT-4 and DALL-E 3
- **Content Processing**: Automated workflow with real-time updates

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key

### Installation

1. **Clone and setup the project**:
```bash
git clone <repository-url>
cd 7cycles-ai
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Node.js dependencies**:
```bash
npm run install-frontend
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Running the Application

1. **Start the backend server**:
```bash
npm run dev-backend
```

2. **Start the frontend development server**:
```bash
npm run dev-frontend
```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Usage

### Generating Content

1. **Navigate to the homepage** and click "Generate Instagram Content"
2. **Monitor progress** as the system:
   - Researches topics from your knowledge files
   - Generates compelling captions with hashtags
   - Creates visual concepts and images
3. **Review and approve** the generated content
4. **Download or use** the approved content for your Instagram posts

### Knowledge Files

Add your content sources to the `knowledge_files/` directory:
- `affirmations.txt` - Daily affirmations and positive content
- `wellness_tips.txt` - Wellness and self-improvement advice
- Add more files as needed

### API Endpoints

- `POST /generate-content` - Start content generation
- `GET /content/{content_id}` - Get content status and results
- `POST /approve-content` - Approve or reject content
- `GET /content` - List all generated content
- `GET /health` - Health check

## Customization

### Adding New Knowledge Files
1. Create new `.txt` files in `knowledge_files/`
2. Update the `ContentRequest` in the frontend to include new files
3. The system will automatically incorporate new knowledge

### Modifying Agents
- **Researcher**: Edit `src/agents/researcher.py`
- **Writer**: Edit `src/agents/writer.py`
- **Image Creator**: Edit `src/agents/image_creator.py`

### Styling and Branding
- Update CSS files in `frontend/src/components/`
- Modify color schemes and layouts to match your brand

## Project Structure

```
7cycles-ai/
├── src/
│   ├── agents/          # CrewAI agents
│   ├── flows/           # CrewAI flows
│   └── tools/           # Utility tools
├── backend/
│   └── main.py          # FastAPI server
├── frontend/
│   └── src/
│       └── components/  # React components
├── knowledge_files/     # Content sources
├── static/
│   └── generated/       # Generated images
└── requirements.txt     # Python dependencies
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   - Ensure your API key is set in `.env`
   - Check API key permissions and billing

2. **Port Conflicts**:
   - Backend runs on port 8000
   - Frontend runs on port 3000
   - Change ports in package.json if needed

3. **CORS Issues**:
   - Backend allows all origins in development
   - Configure CORS settings for production

4. **Image Generation Fails**:
   - Check OpenAI API quota
   - Verify DALL-E 3 model access

### Getting Help

1. Check the API documentation at http://localhost:8000/docs
2. Review logs in the backend console
3. Check browser console for frontend errors

## Production Deployment

### Backend
1. Set production environment variables
2. Configure CORS for your domain
3. Use a production WSGI server (e.g., Gunicorn)

### Frontend
1. Build the React app: `npm run build-frontend`
2. Serve static files with a web server
3. Configure API endpoints for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.