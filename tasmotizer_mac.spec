# -*- mode: python -*-

block_cipher = None

a = Analysis(['tasmotizer.py'],
             binaries=[],
             datas=[('banner.py', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='tasmotizer-1.2.1',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='icon-256.icns')
app = BUNDLE(exe,
             name='tasmotizer-1.2.1.app',
             icon='icon-256.icns',
             bundle_identifier='com.tasmota.tasmotizer')
