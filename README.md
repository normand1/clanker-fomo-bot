# Clanker Token Tracker

A Python application that tracks new token launches on Clanker.world, with support for desktop notifications when tokens are created by influential creators.

## Features

- Monitors new token launches on Clanker.world
- Fetches creator information using the Neynar API
- Displays token data in a clean, colorized terminal output
- Sends desktop notifications for tokens created by users with >8000 followers
- Supports JSON output for data analysis

## Prerequisites

- Python 3.12.3 (recommended to install using `pyenv`)
- Chrome browser (for Selenium WebDriver)
- macOS for desktop notifications (pync dependency)
- Neynar API key (sign up at https://neynar.com)


## Installation

1. **Install pyenv and ensure it's properly configured**:
   - If you haven't installed `pyenv`, follow the instructions on the [pyenv GitHub page](https://github.com/pyenv/pyenv#installation).
   - **Configure your shell environment**:
     - Add the following to your shell's startup script (e.g., `~/.zshrc` or `~/.bashrc`):
       ```bash
       export PYENV_ROOT="$HOME/.pyenv"
       export PATH="$PYENV_ROOT/bin:$PATH"
       eval "$(pyenv init -)"
       ```
     - Restart your terminal or source the startup script:
       ```bash
       source ~/.zshrc  # or source ~/.bashrc
       ```

2. **Install necessary build dependencies** (Linux users only):
   - On Ubuntu/Debian systems:
     ```bash
     sudo apt update
     sudo apt install -y build-essential libssl-dev zlib1g-dev      libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm      libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
     ```

3. **Install Python 3.12.3 using pyenv**:
   - Install Python 3.12.3:
     ```bash
     pyenv install 3.12.3
     ```

4. **Clone the repository**:
   ```bash
   git clone https://github.com/normand1/clanker-token-tracker.git
   cd clanker-token-tracker
   ```

5. **Set Python 3.12.3 for the project**:
   - Use `pyenv` to set Python 3.12.3 for the current project directory:
     ```bash
     pyenv local 3.12.3
     ```

6. **(Optional) Install pyenv-virtualenv**:
   - If you prefer using `pyenv-virtualenv` to manage virtual environments:
     ```bash
     git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
     ```
   - Add the following to your shell's startup script:
     ```bash
     eval "$(pyenv virtualenv-init -)"
     ```
   - Restart your terminal or source the startup script:
     ```bash
     source ~/.zshrc  # or source ~/.bashrc
     ```

7. **Create and activate a virtual environment**:
   - **Using pyenv-virtualenv**:
     ```bash
     pyenv virtualenv 3.12.3 clanker-bot-venv
     pyenv local clanker-bot-venv
     ```
   - **Using venv (default)**:
     ```bash
     python3 -m venv clanker-bot-venv
     source clanker-bot-venv/bin/activate  # On Windows use `clanker-bot-venv\Scripts\activate`
     ```

8. **Upgrade pip and install the required dependencies**:
   - Upgrade `pip`:
     ```bash
     pip install --upgrade pip
     ```
   - Install dependencies from `requirements.txt`:
     ```bash
     pip install -r requirements.txt
     ```

9. **Set up your environment variables**:
   - Copy the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   - **Edit the `.env` file**:
     - Open `.env` in a text editor and fill in the required environment variables (e.g., API keys, database URLs).

10. **Verify the setup**:
    - **Check Python version**:
      ```bash
      python --version
      ```
      - Ensure it outputs `Python 3.12.3`.
    - **Run tests (if applicable)**:
      ```bash
      python -m unittest discover
      ```

11. **Additional project-specific setup** (if applicable):
    - If the project requires database setup, migrations, or other initialization tasks, follow any instructions provided in the project documentation.

---

## Notes
- If you're on Windows and using PowerShell to activate a virtual environment, you may need to adjust the execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Always ensure you’re in the correct virtual environment before running project commands.
- Never commit the `.env` file or sensitive credentials to version control.

## Automation with Cron

To automate the script execution using `crontab` on macOS, follow these steps:

1. Open the Terminal and edit the crontab file:
   ```bash
   crontab -e
   ```

2. Add the following line to schedule the script to run every minute:
   ```bash
   */5 * * * * ~/.pyenv/versions/3.12.3/bin/python3.12 /Users/yourusername/clanker-launch-bot/app.py >> /Users/yourusername/clanker-launch-bot/logfile.log 2>&1
   ```

   - This will execute the script every minute and log the output to `logfile.log`.

3. Save and exit the editor.

4. Verify the cron job is added:
   ```bash
   crontab -l
   ```

## Contribution

Contributions are welcome! If you find a bug or want to add a new feature, please open an issue or submit a pull request.

