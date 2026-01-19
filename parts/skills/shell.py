"""Shell and command execution tools."""
import subprocess


def run_command(command: str, cwd: str | None = None) -> str:
    """Run a shell command and return output.
    
    Args:
        command: The command to run.
        cwd: Working directory (optional).
        
    Returns:
        Command output (stdout + stderr).
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (60s limit)"
    except Exception as e:
        return f"Error running command: {e}"


def git_status(repo_path: str = ".") -> str:
    """Get git status for a repository.
    
    Args:
        repo_path: Path to the git repository.
        
    Returns:
        Git status output.
    """
    return run_command("git status --short", cwd=repo_path)


def git_diff(repo_path: str = ".", staged: bool = False) -> str:
    """Get git diff.
    
    Args:
        repo_path: Path to the git repository.
        staged: If True, show staged changes only.
        
    Returns:
        Git diff output (truncated if large).
    """
    cmd = "git diff --staged" if staged else "git diff"
    result = run_command(cmd, cwd=repo_path)
    # Truncate if too large
    if len(result) > 5000:
        result = result[:5000] + "\n... [truncated, diff too large]"
    return result


def git_log(repo_path: str = ".", count: int = 10) -> str:
    """Get recent git commits.
    
    Args:
        repo_path: Path to the git repository.
        count: Number of commits to show.
        
    Returns:
        Git log output.
    """
    return run_command(f"git log --oneline -n {count}", cwd=repo_path)
