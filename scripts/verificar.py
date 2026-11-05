"""Verificação portátil das camadas Python e JavaScript, sem acessar o Lattes."""
import os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
subprocess.run(['node','scripts/prepare-demo.mjs'],cwd=root,check=True)
commands=[[sys.executable,'-m','unittest','discover','-s','tests','-p',name] for name in ['test_classificacao.py','test_criterios.py','test_orientacoes.py']]
commands.append(['node','scripts/test-unit.mjs'])
for command in commands:
 print('Executando:', ' '.join(command),flush=True)
 subprocess.run(command,cwd=root,check=True)
