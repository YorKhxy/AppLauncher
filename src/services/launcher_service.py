import os
import subprocess
import sys
import webbrowser
import psutil
import time
from urllib.parse import urlparse
from typing import Optional, Dict, List, Set
from models.app_item import AppItem


class LauncherService:
    def __init__(self):
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.temp_bat_files: Dict[str, List[str]] = {}
        self.exe_names_to_kill: Dict[str, Set[str]] = {}
    
    def launch_app(self, app_item: AppItem) -> bool:
        if app_item.kind == "url":
            url = self.normalize_url(app_item.path)
            if not self.validate_url(url):
                return False
            try:
                webbrowser.open(url, new=2)
                return True
            except Exception as e:
                print(f"打开链接失败: {e}")
                return False

        if not self.validate_path(app_item.path):
            return False

        try:
            working_dir = app_item.working_dir if app_item.working_dir else os.path.dirname(app_item.path)
            
            if not working_dir or not os.path.isdir(working_dir):
                working_dir = os.path.dirname(app_item.path)
            
            if not working_dir:
                working_dir = None
            
            file_type = self.get_file_type(app_item.path)
            
            if file_type == 'bat':
                exe_names = self._extract_exe_names_simple(app_item.path)
                self.exe_names_to_kill[app_item.id] = exe_names
                
                temp_bat_path = self._create_fixed_bat(app_item.path)
                self.temp_bat_files[app_item.id] = [temp_bat_path]
                
                process = subprocess.Popen(
                    temp_bat_path,
                    cwd=working_dir,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.running_processes[app_item.id] = process
                return True
            elif file_type == 'exe':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1
                
                exe_name = os.path.splitext(os.path.basename(app_item.path))[0]
                self.exe_names_to_kill[app_item.id] = {exe_name}
                
                process = subprocess.Popen(
                    [app_item.path],
                    cwd=working_dir,
                    shell=False,
                    startupinfo=startupinfo
                )
                
                self.running_processes[app_item.id] = process
                return True
            else:
                os.startfile(app_item.path)
                return True
        except Exception as e:
            print(f"启动应用失败: {e}")
            return False
    
    def _extract_exe_names_simple(self, bat_path: str) -> Set[str]:
        exe_names = set()
        
        try:
            with open(bat_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(bat_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                try:
                    with open(bat_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    return exe_names
        
        lines = content.split('\n')
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            if line_stripped.startswith('rem ') or line_stripped.startswith('@') or line_stripped.startswith('::') or line_stripped.startswith(':'):
                continue
            
            parts = line_stripped.split()
            for part in parts:
                part = part.strip('"')
                if part.lower().endswith('.exe'):
                    exe_name = os.path.splitext(os.path.basename(part))[0]
                    exe_names.add(exe_name)
        
        return exe_names
    
    def _create_fixed_bat(self, original_path: str) -> str:
        bat_dir = os.path.dirname(original_path)
        bat_name = os.path.basename(original_path)
        original_full_path = original_path.replace('/', '\\')
        bat_dir_backslash = bat_dir.replace('/', '\\')
        
        try:
            with open(original_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(original_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                try:
                    with open(original_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    content = ""
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                fixed_lines.append(line)
                continue
            
            if line_stripped.startswith('@') or line_stripped.startswith('rem ') or line_stripped.startswith('::') or line_stripped.startswith(':'):
                fixed_lines.append(line)
                continue
            
            if 'set "target=' in line_stripped.lower() and '%~dp0%~nx0' in line.lower():
                fixed_lines.append(f'set "TARGET={original_full_path}"')
                continue
            
            if 'set "script_dir=' in line_stripped.lower() and '%~dp0' in line.lower():
                fixed_lines.append(f'set "SCRIPT_DIR={bat_dir_backslash}\\"')
                continue
            
            if 'taskkill' in line_stripped.lower():
                continue
            
            if 'stop-process' in line_stripped.lower():
                continue
            
            if line_stripped.lower().startswith('start '):
                fixed_lines.append(line)
                continue
            
            cmd_keywords = ('if ', 'if(', 'echo ', 'echo.', 'set ', 'timeout ', 'pause', 'exit ', 'goto ',
                           'call ', 'cd ', 'chdir ', 'pushd ', 'popd', 'for ', 'title ', 'color ',
                           'choice ', 'find ', 'findstr ', 'type ', 'copy ', 'move ', 'del ', 'erase ',
                           'ren ', 'rename ', 'md ', 'mkdir ', 'rd ', 'rmdir ', 'cls', 'ver', 'date', 'time')
            is_cmd = any(line_stripped.lower().startswith(kw) for kw in cmd_keywords)
            
            has_exe = '.exe' in line_stripped.lower()
            has_start = 'start' in line_stripped.lower()
            
            if has_exe and not has_start and not is_cmd:
                fixed_lines.append('start "" ' + line)
            else:
                fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        temp_file = os.path.join(bat_dir, f'_vrlauncher_{bat_name}')
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return temp_file
    
    def _kill_process_and_children(self, exe_name: str):
        killed_pids = set()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == f"{exe_name}.exe".lower():
                    killed_pids.add(proc.info['pid'])
                    try:
                        parent = psutil.Process(proc.info['pid'])
                        children = parent.children(recursive=True)
                        
                        for child in children:
                            try:
                                child.kill()
                            except:
                                pass
                        
                        parent.kill()
                    except:
                        proc.kill()
            except:
                pass
        
        if killed_pids:
            time.sleep(0.5)
    
    def close_app(self, app_id: str) -> bool:
        success = False
        
        if app_id in self.exe_names_to_kill:
            for exe_name in self.exe_names_to_kill[app_id]:
                try:
                    self._kill_process_and_children(exe_name)
                    success = True
                except Exception as e:
                    print(f"关闭 {exe_name} 失败: {e}")
            
            del self.exe_names_to_kill[app_id]
        
        if app_id in self.running_processes:
            process = self.running_processes[app_id]
            
            try:
                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)
                
                for child in children:
                    try:
                        child.kill()
                    except:
                        pass
                
                process.kill()
                success = True
            except psutil.NoSuchProcess:
                success = True
            except Exception as e:
                print(f"关闭进程失败: {e}")
                try:
                    process.kill()
                    success = True
                except:
                    pass
            
            del self.running_processes[app_id]
        
        if app_id in self.temp_bat_files:
            for temp_file in self.temp_bat_files[app_id]:
                try:
                    os.remove(temp_file)
                except:
                    pass
            del self.temp_bat_files[app_id]
        
        return success
    
    def is_running(self, app_id: str) -> bool:
        if app_id not in self.running_processes:
            return False
        
        process = self.running_processes[app_id]
        return process.poll() is None
    
    @staticmethod
    def validate_path(path: str) -> bool:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        return True

    @staticmethod
    def normalize_url(raw: str) -> str:
        s = (raw or "").strip()
        if not s:
            return ""
        p = urlparse(s)
        if p.scheme in ("http", "https"):
            return s
        if "://" not in s:
            return "https://" + s.lstrip("/")
        return s

    @staticmethod
    def validate_url(url: str) -> bool:
        u = urlparse((url or "").strip())
        return u.scheme in ("http", "https") and bool(u.netloc)

    @staticmethod
    def get_file_type(path: str) -> str:
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        if ext == '.exe':
            return 'exe'
        elif ext == '.bat':
            return 'bat'
        elif ext == '.cmd':
            return 'bat'
        else:
            return 'unknown'

    @staticmethod
    def get_executable_files(path: str) -> list:
        files = []
        try:
            if os.path.isdir(path):
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext in ('.exe', '.bat', '.cmd'):
                            files.append((item, item_path))
        except Exception:
            pass
        return files