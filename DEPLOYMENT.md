# Deployment Guide for Shared Hosting (cPanel/Python)

This guide explains how to deploy QircuitLearn on a shared hosting environment (e.g., Namecheap, Bluehost, SiteGround) that supports Python applications via **Phusion Passenger** (often labeled as "Setup Python App" in cPanel).

## Prerequisites

1.  **Shared Hosting Account** with cPanel and Python support.
2.  **SSH Access** (recommended) or File Manager access.
3.  **MySQL Database** (optional, you can use SQLite for simplicity if file permissions allow).

## Step 1: Upload Files

1.  Create a directory for your app in your home directory (e.g., `/home/username/qircuitlearn`).
2.  Upload all project files **EXCEPT**:
    *   `venv/` (You must create this on the server)
    *   `*.pyc` files or `__pycache__` directories
    *   `.git` folder (optional)
    *   `.env` (You should create a production version manually)

## Step 2: Create Python App in cPanel

1.  Log in to cPanel.
2.  Go to **"Setup Python App"**.
3.  Click **"Create Application"**.
4.  **Python Version**: Choose 3.9 or newer.
5.  **App Directory**: Enter the path where you uploaded files (e.g., `qircuitlearn`).
6.  **App Domain/URI**: Choose your domain (e.g., `qircuit.yourdomain.com`).
7.  **Application Entry Point**: Enter `passenger_wsgi.py`.
    *   *Note: QircuitLearn includes a `passenger_wsgi.py` file specifically for this.*
8.  Click **Create**.

## Step 3: Install Dependencies

1.  In the Python App dashboard in cPanel, copy the "Command for entering virtual environment" (it looks like `source /home/user/virtualenv/qircuitlearn/3.9/bin/activate`).
2.  Connect via SSH (or use the Terminal in cPanel).
3.  Paste the command to activate the virtual environment.
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Step 4: Configure Database

### Option A: SQLite (Simplest)
1.  Ensure `qircuit.db` is uploaded to your app directory.
2.  Ensure the file permissions for `qircuit.db` allow write access by the web server user (usually 644 or 664 is fine, but the *folder* containing it might need write permissions if the DB uses WAL mode).
3.  Set `DB_TYPE=sqlite` in your environment variables (or `.env` file).

### Option B: MySQL (Recommended for Production)
1.  Create a MySQL database and user in cPanel.
2.  Import `schema.sql` into your MySQL database using phpMyAdmin.
3.  Create a `.env` file in your app root with the following:
    ```ini
    DB_TYPE=mysql
    DB_HOST=localhost
    DB_USER=your_db_user
    DB_PASS=your_db_password
    DB_NAME=your_db_name
    SECRET_KEY=your_secure_random_string
    ```

## Step 5: Static Files

Most shared hosting setups serve static files (CSS/JS/Images) directly via Nginx/Apache, bypassing Python for performance.

1.  In cPanel "Setup Python App", look for **Configuration files** or **Static files** section (if available).
2.  Or, create an `.htaccess` file in your `public_html` (or wherever the domain points) to handle static files if they aren't loading.
    *   However, Flask will serve static files from `/static` automatically if not intercepted by the web server.
    *   If images/styles are missing, you may need to symlink the `static` folder to `public_html/static`.

    ```bash
    ln -s /home/username/qircuitlearn/static /home/username/public_html/static
    ```

## Step 6: Restart Application

1.  Go back to cPanel "Setup Python App".
2.  Click **Restart**.

## Troubleshooting

-   **500 Internal Server Error**: Check the `stderr.log` in your app directory.
-   **Database Errors**: Ensure your connection string in `.env` is correct.
-   **Missing Images**: Check if the `static/` folder is accessible via the browser URL.

## Image Support
This platform supports serving images from the `static/images` directory. To add images to lessons:
1. Upload images to `static/images`.
2. Reference them in lesson content HTML: `<img src="/static/images/my-diagram.png" alt="Diagram">`.
