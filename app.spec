# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_all, collect_submodules

# 1) 本地资源（请按你的实际路径保持相对层级）
datas = [
    ('data', 'data'),
    ('src', 'src'),
    ('config.json', '.'),
    ('static', 'static'),
    # 本地离线模型与知识库索引
    ('src/models/bge-small-zh-v1.5', 'src/models/bge-small-zh-v1.5'),
    ('src/knowledge_base/knowledge_data', 'src/knowledge_base/knowledge_data'),
    ('src/knowledge_base/rag_index', 'src/knowledge_base/rag_index'),
    ('src/knowledge_base/core', 'src/knowledge_base/core'),
]

binaries = []
hiddenimports = [
    'hnswlib',
    'numpy',
    'sentence_transformers.SentenceTransformer',
    'transformers.models.auto',
    'transformers.tokenization_utils',
    'transformers.modeling_utils'
]

# 2) 核心三方库的收集（尽量完整）
# sentence_transformers/transformers/tokenizers/huggingface_hub/safetensors/filelock/packaging/regex/tqdm
for pkg in [
    'sentence_transformers', 'transformers', 'tokenizers', 'huggingface_hub',
    'safetensors', 'filelock', 'packaging', 'regex', 'tqdm'
]:
    da, bi, hi = collect_all(pkg)
    datas += da
    binaries += bi
    hiddenimports += hi

# 3) numpy/scipy（如未用 scipy 可去掉），以及它们的子模块（动态导入）
hiddenimports += collect_submodules('numpy')
try:
    hiddenimports += collect_submodules('scipy')
    da, bi, hi = collect_all('scipy')
    datas += da; binaries += bi; hiddenimports += hi
except Exception:
    pass

# 4) hnswlib 的二进制与数据
datas += collect_data_files('hnswlib')
binaries += collect_dynamic_libs('hnswlib')
# 确保包含Windows下vc_redist
binaries += [('C:\\Windows\\System32\\vcruntime140.dll', '.')]

# 5) tokenizers 的二进制
binaries += collect_dynamic_libs('tokenizers')

# 6) 如果你使用 MKL 或 OpenMP，PyInstaller 一般能带上；如遇到缺 DLL 可手工加：
# binaries += collect_dynamic_libs('numpy')

a = Analysis(
    ['app.py'],
    pathex=['.'],          # 确保包含你的项目根目录
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    excludes=['PyQt5','PyQt6'],
    noarchive=True,        # 建议 True：便于动态导入（zip 内导入更容易失败）
    optimize=0,
    runtime_hooks=['rthook_fix_numpy.py'] # ← 加这一行
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
