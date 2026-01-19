"""System awareness tools - local machine info."""
import platform
import subprocess


def system_info(**kwargs) -> str:
    """Get system information (OS, CPU, memory, GPU)."""
    # Accept **kwargs to ignore LLM's wrong argument guesses
    info = []
    info.append(f"OS: {platform.system()} {platform.release()}")
    info.append(f"Machine: {platform.machine()}")
    info.append(f"Python: {platform.python_version()}")
    
    # Memory (Windows)
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["powershell", "-Command", 
                 "(Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize | Format-List)"],
                capture_output=True, text=True, timeout=5
            )
            info.append(f"Memory:\n{result.stdout.strip()}")
        except:
            pass
    
    # GPU via nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            info.append(f"GPU: {result.stdout.strip()}")
    except:
        info.append("GPU: nvidia-smi not available")
    
    return "\n".join(info)


def list_ports() -> str:
    """List listening TCP ports."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             "Get-NetTCPConnection -State Listen | Select-Object LocalPort,OwningProcess | Sort-Object LocalPort | Format-Table -AutoSize"],
            capture_output=True, text=True, timeout=10
        )
        return f"Listening ports:\n{result.stdout.strip()}"
    except Exception as e:
        return f"Error: {e}"


def running_processes(filter_term: str = "") -> str:
    """List running processes, optionally filtered.
    
    Args:
        filter_term: Optional filter (e.g., "python", "node")
    """
    try:
        cmd = "Get-Process | Select-Object Name,Id,CPU,WorkingSet | Sort-Object CPU -Descending | Select-Object -First 20"
        if filter_term:
            cmd = f"Get-Process | Where-Object {{$_.Name -like '*{filter_term}*'}} | Select-Object Name,Id,CPU,WorkingSet"
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True, text=True, timeout=10
        )
        return f"Processes:\n{result.stdout.strip()}"
    except Exception as e:
        return f"Error: {e}"


def ollama_status() -> str:
    """Check Ollama server and available models."""
    try:
        import ollama
        models = ollama.list()
        model_names = [m.get("name", m.get("model", "?")) for m in models.get("models", [])]
        return f"Ollama running. Models: {', '.join(model_names)}"
    except Exception as e:
        return f"Ollama error: {e}"
