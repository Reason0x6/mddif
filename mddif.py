#!/usr/bin/env python3

import argparse
import configparser
import subprocess
import sys
import os
import pathlib # For path manipulation and home directory
# Removed urllib imports

# --- Constants ---
CONFIG_SECTION = "Markdown"
# Keep the URL constant for the warning message
DEFAULT_CONFIG_URL = "https://gist.githubusercontent.com/Reason0x6/7ac0814373f017c3ce4c04f1833e4a04/raw/7c931dbc26e5de0f2fda0a4ee1bfb38c887e6866/mddif_default_config"

# --- Determine Default Config Path ---
HOME_DIR = pathlib.Path.home()
DEFAULT_CONFIG_DIR = HOME_DIR / "mddif"
CONFIG_FILE_DEFAULT_PATH = DEFAULT_CONFIG_DIR / "diff_config.ini"
CONFIG_FILE_DEFAULT = str(CONFIG_FILE_DEFAULT_PATH) # String version for argparse

# --- Git Command Execution ---
def run_git_command(command, check=True):
    """
    Helper function to run a Git command and handle common errors.
    Returns stdout on success, None on failure if check=False.
    Exits script on failure if check=True.
    """
    try:
        is_rev_parse_check = (len(command) > 2 and command[1] == "rev-parse" and command[2] == "--is-inside-work-tree")
        if not is_rev_parse_check:
             subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True, text=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            )
        result = subprocess.run(
            command, check=check, capture_output=True, text=True, encoding="utf-8",
        )
        return result.stdout
    except FileNotFoundError:
        print("Error: 'git' command not found. Is Git installed?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        if check:
            if "is-inside-work-tree" in str(e.cmd):
                print("Error: Must be run inside a Git repository.", file=sys.stderr)
            else:
                print(f"Error running command: {' '.join(command)}", file=sys.stderr)
                if e.stderr: print(f"Git stderr:\n{e.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return None
    except Exception as e:
        print(f"An unexpected error occurred running git: {e}", file=sys.stderr)
        sys.exit(1)
    # This part is only reached if check=False and CalledProcessError occurred
    return None

# --- Git Diff Logic ---
def run_git_diff(target_branch):
    """
    Fetches updates, checks if HEAD is behind the target, runs git diff,
    and returns the diff output string or None if diff fails.
    """
    print("Fetching updates from origin...", file=sys.stderr)
    run_git_command(["git", "fetch", "origin"])

    print(f"Checking status relative to '{target_branch}'...", file=sys.stderr)
    rev_list_command = ["git", "rev-list", "--left-right", "--count", f"HEAD...{target_branch}"]
    count_output = run_git_command(rev_list_command, check=False)

    if count_output is not None:
        try:
            counts = count_output.strip().split('\t')
            if len(counts) == 2:
                behind_count = int(counts[1])
                if behind_count > 0:
                    print(f"\n!!! WARNING: HEAD is behind '{target_branch}' by {behind_count} commit(s). !!!\n", file=sys.stderr)
            else: print(f"Warning: Could not parse commit counts: '{count_output.strip()}'", file=sys.stderr)
        except (ValueError, IndexError) as e: print(f"Warning: Error parsing commit counts '{count_output.strip()}': {e}", file=sys.stderr)
    else: print(f"Warning: Could not determine relationship between HEAD and '{target_branch}'.", file=sys.stderr)

    print(f"Generating diff between '{target_branch}' and HEAD...", file=sys.stderr)
    diff_command = ["git", "diff", f"{target_branch}..HEAD"]
    diff_output = run_git_command(diff_command)
    return diff_output

# --- Config Reading (Modified) ---
def read_config(config_path):
    """
    Reads prepend/append text from the config file.
    Warns with download link if default config is missing.
    Handles file not found and parsing errors gracefully.
    """
    prepend_text = ""
    append_text = ""
    config_path_obj = pathlib.Path(config_path).expanduser()

    if not config_path_obj.is_file():
        # Check if the missing file is the default one
        if str(config_path_obj) == CONFIG_FILE_DEFAULT:
            # Print specific warning for missing default config
            print(f"\n--- Configuration Warning ---", file=sys.stderr)
            print(f"Default config file not found at: {config_path_obj}", file=sys.stderr)
            print(f"To use a default template, download it from:", file=sys.stderr)
            print(f"  {DEFAULT_CONFIG_URL}", file=sys.stderr)
            print(f"and place it as '{config_path_obj.name}' in the directory:", file=sys.stderr)
            print(f"  {config_path_obj.parent}", file=sys.stderr)
            print(f"You may need to create the directory first.", file=sys.stderr)
            print(f"Proceeding with no prepend/append text.", file=sys.stderr)
            print(f"-----------------------------\n", file=sys.stderr)
        else:
            # Generic message if a user-specified file via -c is missing
             print(f"Info: Specified config file '{config_path_obj}' not found. Using defaults.", file=sys.stderr)
        # Return empty strings as no config was loaded
        return prepend_text, append_text

    # Proceed if file exists
    config = configparser.ConfigParser()
    try:
        config.read(config_path_obj, encoding='utf-8')
        if CONFIG_SECTION in config:
            prepend_text = config[CONFIG_SECTION].get("prepend_text", "").strip()
            append_text = config[CONFIG_SECTION].get("append_text", "").strip()
            if prepend_text: prepend_text += "\n\n"
            if append_text: append_text = "\n\n" + append_text
    except configparser.Error as e:
        print(f"Error reading config file '{config_path_obj}': {e}", file=sys.stderr)
        # Continue with empty defaults if config is broken

    return prepend_text, append_text

# --- Markdown Formatting ---
def format_markdown(diff_output, prepend_text, append_text):
    """Formats the diff output into Markdown."""
    if not diff_output or not diff_output.strip():
        diff_block = "*(No differences found between specified refs)*"
    else:
        diff_block = f"```diff\n{diff_output.strip()}\n```"
    return f"{prepend_text}{diff_block}{append_text}"

# --- Main Execution (Modified) ---
def main():
    parser = argparse.ArgumentParser(
        description="Generate a Markdown formatted diff between a target Git ref and HEAD.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    branch_group = parser.add_mutually_exclusive_group(required=True)
    branch_group.add_argument("-m", "--master", action="store_true", help="Compare HEAD against origin/master.")
    branch_group.add_argument("-rc", "--release-candidate", action="store_true", help="Compare HEAD against origin/Release-Candidate.")
    branch_group.add_argument("-b", "--branch", metavar="BRANCH_OR_REF", help="Compare HEAD against the specified ref.")
    parser.add_argument("-o", "--output", metavar="FILE", help="Output file path. Prints to stdout if not specified.")
    parser.add_argument("-c", "--config", metavar="FILE", default=CONFIG_FILE_DEFAULT, help=f"Path to config file.\n(Default: {CONFIG_FILE_DEFAULT})")

    args = parser.parse_args()

    # --- Removed default directory creation block ---

    # Determine target branch
    target_branch = None
    if args.master: target_branch = "origin/master"
    elif args.release_candidate: target_branch = "origin/Release-Candidate"
    elif args.branch: target_branch = args.branch

    # Core Logic
    # read_config now handles the warning if default is missing
    prepend_text, append_text = read_config(args.config)
    diff_output = run_git_diff(target_branch)
    markdown_content = format_markdown(diff_output, prepend_text, append_text)

    # Output Handling
    if args.output:
        try:
            output_path_obj = pathlib.Path(args.output)
            output_dir = output_path_obj.parent
            if not output_dir.exists():
                 print(f"Info: Creating output directory: {output_dir}", file=sys.stderr)
                 output_dir.mkdir(parents=True, exist_ok=True)
            with output_path_obj.open("w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"Markdown diff successfully written to '{args.output}'", file=sys.stderr)
            try:
                absolute_path = output_path_obj.resolve(strict=True)
                file_uri = absolute_path.as_uri()
                print(f"Link: {file_uri}", file=sys.stderr)
            except Exception as path_e: print(f"(Warning: Could not generate clickable link: {path_e})", file=sys.stderr)
        except (IOError, OSError) as e:
            print(f"Error writing output file/directory '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(markdown_content)

if __name__ == "__main__":
    main()
