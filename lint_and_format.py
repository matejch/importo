import subprocess
import sys


def get_changed_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"], capture_output=True, text=True
    )
    return [file for file in result.stdout.split("\n") if file.endswith(".py")]


def run_tool(tool, *args):
    try:
        result = subprocess.run([tool, *args], capture_output=True, text=True, check=True)
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def lint_and_format_file(file_path):
    print(f"Processing {file_path}")
    errors_found = False

    # Run isort
    success, stdout, stderr = run_tool("isort", file_path)
    if not success:
        print(f"Error running isort:\n{stderr}")
        errors_found = True

    # Run Black
    success, stdout, stderr = run_tool("black", file_path)
    if not success:
        print(f"Error running black:\n{stderr}")
        errors_found = True

    # Run Ruff
    success, stdout, stderr = run_tool("ruff", "check", file_path)
    if not success:
        print(f"Ruff found issues:\n{stdout}")
        errors_found = True

    # Run MyPy
    success, stdout, stderr = run_tool("mypy", file_path)
    if not success:
        print(f"MyPy found issues:\n{stdout}")
        errors_found = True

    if not errors_found:
        print(f"No issues found in {file_path}")


def main():
    changed_files = get_changed_files()

    if not changed_files:
        print("No Python files changed.")
        return

    for file in changed_files:
        lint_and_format_file(file)


if __name__ == "__main__":
    main()
