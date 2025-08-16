# rthook_fix_numpy.py
import sys, os

def _maybe_add_dll_dir(p):
    if not (sys.platform.startswith("win") and os.path.isdir(p)):
        return False
    try:
        # Python 3.8+：更靠谱的方式
        os.add_dll_directory(p)  # type: ignore[attr-defined]
    except Exception:
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
    return True

if getattr(sys, "frozen", False):
    base = os.path.dirname(sys.executable)
    # 可能的 numpy.libs 位置：顶层 或 _internal/ 里
    candidates = [
        os.path.join(base, "numpy.libs"),
        os.path.join(base, "_internal", "numpy.libs"),
    ]
    # 保险：遍历查找（不同 PyInstaller 版本/平台布局会变）
    for root, dirs, files in os.walk(base):
        if root.endswith("numpy.libs"):
            candidates.insert(0, root)
            break

    for d in candidates:
        if _maybe_add_dll_dir(d):
            break

    # 纯 Python 包路径也加一下（一般 PyInstaller 已加，这里双保险）
    internal = os.path.join(base, "_internal")
    if os.path.isdir(internal) and internal not in sys.path:
        sys.path.insert(0, internal)
