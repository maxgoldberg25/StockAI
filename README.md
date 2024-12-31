# StockAI
AI agent that makes informed decisions regarding stocks to purchase given recent company news.

## Features
- Analyze recent company news to make stock purchase decisions.
- Utilizes natural language processing (NLP) for sentiment analysis.
- Integrates with financial data APIs for real-time information.

## Installation

### Clone the repository:
```bash
git clone https://github.com/maxgoldberg25/StockAI.git
cd StockAI
```

### Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage
Run the main script to start the AI agent:
```bash
python main.py
```
The agent will analyze recent news and make stock purchase recommendations.

## Configuration
Customize the `config.json` file to set API keys and other parameters.

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Commit your changes:
   ```bash
   git commit -am 'Add new feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature-branch
   ```
5. Create a new Pull Request.
