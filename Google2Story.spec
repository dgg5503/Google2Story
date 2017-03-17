# -*- mode: python -*-

block_cipher = None


a = Analysis(['Google2Story.py'],
             pathex=['C:\\Projects\\Google2Story'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Google2Story',
          debug=False,
          strip=False,
          upx=False,
          console=True )
