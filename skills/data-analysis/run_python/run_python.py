import subprocess
import sys
import os
import json
import tempfile
import traceback
from pathlib import Path


def run(script: str, script_args: dict = None, timeout: int = 60, work_dir: str = None, **kwargs) -> dict:
    """
    Execute a Python script and return results.
    
    Args:
        script: Python script code to execute
        script_args: Optional dict of arguments accessible as 'args' in script
        timeout: Execution timeout in seconds (default: 60)
        work_dir: Working directory for script execution
    
    Returns:
        dict with stdout, stderr, return_code, and result
    """
    if not script or not script.strip():
        return {
            'success': False,
            'error': 'Empty script provided',
            'stdout': '',
            'stderr': '',
            'return_code': -1
        }
    
    # Create a wrapper script that:
    # 1. Injects args variable
    # 2. Captures the last expression or 'result' variable
    # 3. Prints structured output
    
    wrapper_parts = []
    
    # Add common imports
    wrapper_parts.append('''
import sys
import json
import os

# Make args available to the script
args = {}
'''.format(json.dumps(script_args or {})))
    
    # Add the user script
    wrapper_parts.append('\n# === User Script Start ===\n')
    wrapper_parts.append(script)
    wrapper_parts.append('\n# === User Script End ===\n')
    
    # Add result capture
    wrapper_parts.append('''
# Try to capture 'result' variable if defined
try:
    if 'result' in dir() or 'result' in locals():
        _result = locals().get('result', None)
        if _result is not None:
            print('\\n__RESULT_START__')
            if isinstance(_result, (dict, list, tuple, int, float, str, bool)):
                print(json.dumps(_result, ensure_ascii=False, default=str))
            else:
                print(str(_result))
            print('__RESULT_END__')
except Exception:
    pass
''')
    
    full_script = '\n'.join(wrapper_parts)
    
    # Write to temp file
    tmp_dir = work_dir or tempfile.gettempdir()
    script_path = os.path.join(tmp_dir, '_goldminer_run_python.py')
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(full_script)
        
        # Execute the script
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir,
            env=env
        )
        
        stdout = proc.stdout or ''
        stderr = proc.stderr or ''
        return_code = proc.returncode
        
        # Extract structured result if present
        extracted_result = None
        display_stdout = stdout
        
        if '__RESULT_START__' in stdout and '__RESULT_END__' in stdout:
            start_idx = stdout.index('__RESULT_START__') + len('__RESULT_START__\n')
            end_idx = stdout.index('__RESULT_END__')
            result_str = stdout[start_idx:end_idx].strip()
            
            # Remove result markers from display output
            display_stdout = stdout[:stdout.index('\n__RESULT_START__')]
            
            try:
                extracted_result = json.loads(result_str)
            except json.JSONDecodeError:
                extracted_result = result_str
        
        return {
            'success': return_code == 0,
            'stdout': display_stdout.strip(),
            'stderr': stderr.strip(),
            'return_code': return_code,
            'result': extracted_result,
            'error': stderr.strip() if return_code != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'Script execution timed out after {timeout} seconds',
            'stdout': '',
            'stderr': f'TimeoutError: exceeded {timeout}s limit',
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'stdout': '',
            'stderr': traceback.format_exc(),
            'return_code': -1
        }
    finally:
        # Cleanup temp file
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
        except OSError:
            pass
