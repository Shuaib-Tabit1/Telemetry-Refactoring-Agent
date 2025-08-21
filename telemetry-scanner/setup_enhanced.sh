#!/bin/bash

# Enhanced Telemetry Agent Setup Script
echo "🚀 Setting up Enhanced Telemetry Refactoring Agent..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '\d+\.\d+' | head -1)
required_version="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo "❌ Python 3.9+ required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install enhanced requirements
echo "📋 Installing enhanced dependencies..."
pip install -r requirements-enhanced.txt

# Install existing requirements (if they exist)
if [ -f "requirements.txt" ]; then
    echo "📋 Installing existing dependencies..."
    pip install -r requirements.txt
fi

# Download required models
echo "🤖 Downloading sentence transformer models..."
python3 -c "
from sentence_transformers import SentenceTransformer
print('Downloading all-MiniLM-L6-v2...')
SentenceTransformer('all-MiniLM-L6-v2')
print('Downloading all-mpnet-base-v2...')
SentenceTransformer('all-mpnet-base-v2')
print('✅ Models downloaded successfully')
"

# Build C# CodeGraphBuilder if needed
if [ -d "../CodeGraphBuilder" ]; then
    echo "🔨 Building C# CodeGraphBuilder..."
    cd ../CodeGraphBuilder
    if command -v dotnet &> /dev/null; then
        dotnet build -c Release
        echo "✅ CodeGraphBuilder built successfully"
    else
        echo "⚠️  .NET SDK not found. Please build CodeGraphBuilder manually:"
        echo "   cd ../CodeGraphBuilder && dotnet build -c Release"
    fi
    cd ../telemetry-scanner
fi

# Create output directories
echo "📁 Creating output directories..."
mkdir -p runs/enhanced-run
mkdir -p cache
mkdir -p logs

# Create environment file template
if [ ! -f ".env" ]; then
    echo "🔐 Creating environment template..."
    cat > .env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Jira Configuration
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Enhanced Agent Configuration
TELEMETRY_AGENT_CACHE_DIR=./cache
TELEMETRY_AGENT_LOG_LEVEL=INFO
TELEMETRY_AGENT_MAX_WORKERS=4
EOF
    echo "⚠️  Please update .env file with your actual credentials"
fi

# Run basic validation
echo "🧪 Running basic validation..."
python3 -c "
import sys
import importlib

required_modules = [
    'numpy', 'networkx', 'openai', 'sklearn', 'sentence_transformers', 
    'pandas', 'matplotlib', 'pydantic', 'asyncio', 'pathlib'
]

missing_modules = []
for module in required_modules:
    try:
        importlib.import_module(module)
        print(f'✅ {module}')
    except ImportError:
        missing_modules.append(module)
        print(f'❌ {module}')

if missing_modules:
    print(f'Missing modules: {missing_modules}')
    sys.exit(1)
else:
    print('🎉 All required modules available!')
"

echo ""
echo "🎉 Enhanced Telemetry Agent setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env file with your credentials"
echo "2. Test the enhanced CLI:"
echo "   python3 enhanced_cli.py --help"
echo "3. Run a test with your monorepo:"
echo "   python3 enhanced_cli.py --ticket-key YOUR-TICKET --repo-root /path/to/repo --dirs-proj-path /path/to/dirs.proj"
echo ""
echo "📚 Features available:"
echo "   • Enhanced intent extraction with confidence scoring"
echo "   • Multi-modal intelligent search"
echo "   • Advanced code graph analysis with architectural patterns"
echo "   • Chain-of-thought LLM reasoning"
echo "   • Comprehensive validation framework"
echo "   • Robust pipeline orchestration with caching"
echo "   • Detailed impact analysis and reporting"
