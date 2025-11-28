# Deploying QircuitLearn on cPanel Shared Hosting

This guide walks you through deploying the QircuitLearn platform to a shared hosting environment using cPanel's **"Setup Python App"** feature.

## Prerequisites

*   A cPanel hosting account.
*   **"Setup Python App"** icon available in your cPanel dashboard (CloudLinux).
*   Access to File Manager or FTP.

## Option A: Git Deployment (Recommended)

If you have used cPanel's **Git Version Control** to clone your repository to a folder (e.g., `public_html/Qircuit`), follow these steps:

1.  **Create Python App**:
    *   Go to **"Setup Python App"**.
    *   **Application Root**: Enter the path where you cloned the repo (e.g., `public_html/Qircuit`).
    *   **Application Startup File**: `passenger_wsgi.py`.
    *   **Application Entry Point**: `application`.
    *   Click **Create**.

2.  **Install Dependencies**:
    *   In the App configuration, add `requirements.txt` and click **Run Pip Install**.

3.  **Initialize Database (Crucial)**:
    *   Since `qircuit.db` is ignored by Git, you must generate it on the server.
    *   **Method 1 (SSH)**:
        Run the command provided by cPanel (example below) to enter the environment, then run the seed script:
        ```bash
        # Replace with your specific command from cPanel
        source /home/qircuitc/virtualenv/public_html/Qircuit/3.11/bin/activate && cd /home/qircuitc/public_html/Qircuit
        
        # Then initialize the database
        python seed.py
        ```
    *   **Method 2 (Cron Job workaround)**:
        *   If you don't have SSH, create a Cron Job to run `python /path/to/public_html/Qircuit/seed.py` once, then delete the job.

## Option B: Manual File Upload

1.  **Prepare the Application Locally**


1.  **Ensure you have the database ready.**
    *   Run `python seed.py` locally to create the latest `qircuit.db` file.
    *   This file contains all the lessons and curriculum.

2.  **Zip the project files.**
    *   Select all files in your project folder **EXCEPT** `venv`, `.git`, `.idea`, `__pycache__`.
    *   Create a zip archive (e.g., `qircuit_app.zip`).
    *   *Critical files to include:* `app/`, `static/`, `templates/`, `passenger_wsgi.py`, `requirements.txt`, `qircuit.db`, `.env` (if you have one, or create it later).

## Step 2: Create Python App in cPanel

1.  Log in to **cPanel**.
2.  Find and click **"Setup Python App"**.
3.  Click **"Create Application"**.
4.  **Python Version**: Select **3.9** or newer (recommended).
5.  **Application Root**: Enter the path where files will live (e.g., `qircuitlearn`).
6.  **Application URL**: Select your domain (e.g., `qircuitlearn.com`).
7.  **Application Startup File**: Enter `passenger_wsgi.py`.
8.  **Application Entry Point**: Enter `application` (this matches the variable in `passenger_wsgi.py`).
9.  Click **Create**.

## Step 3: Upload Files

1.  Go to **File Manager** in cPanel.
2.  Navigate to the **Application Root** folder you defined (e.g., `/home/username/qircuitlearn`).
3.  **Delete** the default `passenger_wsgi.py` created by cPanel (it's just a placeholder).
4.  **Upload** your `qircuit_app.zip` file.
5.  **Extract** the zip file into this folder.
6.  Ensure `passenger_wsgi.py`, `qircuit.db`, and the `app/` folder are in the root of this directory.

## Step 4: Install Dependencies

1.  Go back to the **"Setup Python App"** page in cPanel.
2.  Find your application in the list and click the **Edit** (pencil) icon.
3.  Scroll down to the "Configuration files" section.
4.  Enter `requirements.txt` and click **Add**.
5.  Click the **Run Pip Install** button.
    *   *Wait for it to complete. This installs Flask, Cirq, etc.*

## Step 5: Final Configuration & Restart

1.  **Database Permission Check**:
    *   Ensure the `qircuit.db` file has write permissions if you plan to update it (though for this app, it's mostly read-only for users).
    *   In File Manager, check permissions are usually `644`.

2.  **Restart the App**:
    *   On the Python App page, click the **Restart** button.

## Step 6: Verify

1.  Open your website URL.
2.  You should see the QircuitLearn landing page.
3.  Try dragging a gate in the simulator to ensure everything works.

## Troubleshooting

*   **"Can't acquire lock for app" Error**:
    *   This means a process (like a previous pip install or deployment) is stuck.
    *   **Fix via SSH**:
        1.  Run `pkill -f python` to stop all running Python processes for your user.
        2.  Run `pkill -f passenger` to stop the app server.
        3.  Wait 1-2 minutes.
        4.  Try the operation again (e.g., Run Pip Install or Restart).
    *   If that fails, contact your hosting support to clear the lock for your user.

*   **"Internal Server Error"**:
    *   Check the `stderr.log` in your application root folder.
    *   Common issue: Missing dependencies. Try running pip install again.
    *   Common issue: Path errors. Ensure `passenger_wsgi.py` imports `application` correctly.

*   **Images/CSS not loading**:
    *   Ensure the `static` folder is correctly uploaded.
    *   Flask automatically serves static files from the `static` folder.

*   **Database not found**:
    *   The app looks for `qircuit.db` in the parent directory of `app/`. Since you uploaded it to the application root, it should work.

*   **"Update to latest version" Warning/Error**:
    *   **Scenario**: You see a message about updating to the latest version when running `seed.py` or installing requirements.
    *   **Cause**: This is often a warning from `pip` (Python's package installer) telling you a new version is available (e.g., `[notice] A new release of pip is available`).
    *   **Solution**:
        1.  **It's usually just a warning.** If the script (`seed.py`) still ran and printed "Initializing database...", you can ignore it.
        2.  **If it blocks execution**: Run the upgrade command suggested in the message, usually:
            ```bash
            pip install --upgrade pip
            ```
        3.  **Check Python Version**: Ensure your cPanel Python App is set to **3.9+** (3.11 is ideal). Older versions might be deprecated.
