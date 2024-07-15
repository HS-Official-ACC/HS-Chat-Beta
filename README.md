# HS-Chat-Beta

# Discord Bot Setup Instructions

## Required Installations

Before you begin, ensure you have the following installed:

- **Python**: The bot is written in Python. You'll need Python 3.6 or higher.
- **discord.py**: A Python library for interacting with Discord's API.
- **transformers**: This library by Hugging Face is used for the DialoGPT model.
- **torch**: Also known as PyTorch, this is used for machine learning and working with the DialoGPT model.
- **asyncio**: Included in the Python standard library, used for writing concurrent code.
- **logging**: Also included in the Python standard library, used for logging messages.
- **json**: Part of the Python standard library, used for working with JSON data.

## How to Run the Code

1. **Install Python**:
   Download and install Python from the official website. Make sure to add Python to your system's PATH.

2. **Install Dependencies**:
   Open your command prompt or terminal and install the required libraries using pip:
   ```bash
   pip install discord.py
   pip install transformers
   pip install torch

## Set Up Your Bot Token

Replace the placeholder token in the `client.run('your_token')` line with your actual Discord bot token.

For Replit users:
```python
client.run(os.getenv('SECRET_KEY'))

**Run Your File**
```python
python main.py
