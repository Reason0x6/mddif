# Git Diff to Markdown CLI (mddif)

A command-line tool to generate a Markdown-formatted diff between a specified target Git branch/ref (like master, Release-Candidate, or any other branch/tag) and the current `HEAD`. It incorporates customizable prepend/append text from a configuration file, making it useful for generating change reports, pull request summaries, or documentation snippets.

## Features

*   Generates `git diff` output between a target ref and `HEAD`.
*   Select target ref easily using flags:
    *   `-m` for `origin/master`
    *   `-rc` for `origin/Release-Candidate`
    *   `-b` for any custom branch, tag, or ref.
*   Automatically fetches from `origin` before diffing to ensure refs are up-to-date.
*   Warns if the current `HEAD` is behind the target branch, indicating potentially missing changes in the diff.
*   Formats the diff within a Markdown `diff` code block for syntax highlighting.
*   Supports prepending and appending custom text (titles, context, review prompts, instructions) via an `.ini` config file.
*   **Provides a warning with a download link if the default config file is missing.**
*   Outputs the final Markdown to standard output or a specified file.
*   Provides a clickable `file://` link to the output file in supported terminals.
*   Basic error handling (Git not found, not run in a repo, invalid refs).

## Prerequisites

*   **Python 3.x:** The script is written in Python 3.
*   **Git:** Git must be installed and accessible in your system's PATH.

## Installation / Setup

1.  **Download:** Place the `git_diff_md.py` script in your desired location (e.g., a project's utility folder, or a directory in your system PATH like `~/bin` or `C:\Users\YourUser\Scripts`).
    *   *A sample `diff_config.ini` may be included alongside the script for your convenience.*
2.  **Make Executable (Linux/macOS):**
    ```bash
    chmod +x git_diff_md.py
    ```
    (Windows users will typically run the script using `python git_diff_md.py ...`)
3.  **Configuration File (Optional):**
    *   The script looks for a configuration file by default in a directory named `mddif` within your user's home directory (`~/mddif/diff_config.ini` on Linux/macOS, `C:\Users\<YourUser>\mddif\diff_config.ini` on Windows).
    *   **If this default file is not found**, the script will print a warning message containing a link to download a sample configuration. You would then need to manually create the `~/mddif` directory (if it doesn't exist) and save the downloaded file as `diff_config.ini` inside it.
    *   Alternatively, you can use the `-c` option to specify any other path to a config file, or use the sample `diff_config.ini` provided with the script by placing it in the default location or pointing to it with `-c`. See the [Configuration](#configuration) section below for file format details.

## Usage

Run the script from *within a Git repository*.

**Basic Syntax:**

```bash
# On Linux/macOS (if executable and in PATH or current dir)
git_diff_md.py <branch_flag> [options]

# On Windows (or if not executable/in PATH)
python git_diff_md.py <branch_flag> [options]
