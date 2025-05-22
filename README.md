# Project Overview

This project is a workflow-based system that utilizes various agents to analyze and provide insights on stock market data. The system is built using the Llama Index framework and leverages the Google GenAI model for natural language processing.

# Setup

### Prerequisites

* Python 3.8 or later
* [uv package manager](https://docs.astral.sh/uv/)
* Google GenAI API credentials (obtainable through the Google Cloud Console)

### Installation

1. Clone the repository: `git clone https://github.com/dobraga/ai-investor`
2. Install dependencies: `uv sync`
3. Set up Google GenAI API credentials
4. [Set up AlhaVantage API credential](https://www.alphavantage.co/support/#api-key)
5. Create a new file named `.env` in the project root directory
   
```.env
ALPHA_VANTAGE=
GOOGLE_API_KEY=
```

# Usage

### Running the Workflow

1. Navigate to the project root directory
2. Run the workflow using the following command: `uv run src/`

### Available Agents

The following agents are currently available:

* Warren Buffett Agent
* Ray Dalio Agent
* Peter Lynch Agent
* Cathie Wood Agent
* Fundamentalist Agent
