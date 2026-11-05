"""Empacota a interface existente com Worker e migrações D1, sem reconstruí-la."""
import argparse,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--saida',type=Path,required=True);args=p.parse_args();out=args.saida
if out.resolve()==root.resolve() or root.resolve() in out.resolve().parents:raise ValueError('Use uma saída fora do checkout para o pacote')
if out.exists():shutil.rmtree(out)
(out/'dist/server').mkdir(parents=True);(out/'dist/.openai').mkdir(parents=True)
shutil.copytree(root/'dist',out/'dist/client');shutil.copy2(root/'worker/index.mjs',out/'dist/server/index.js');shutil.copy2(root/'.openai/hosting.json',out/'dist/.openai/hosting.json');shutil.copytree(root/'drizzle',out/'dist/.openai/drizzle')
# The root manifest retains the exact Site identity for archive validation.
shutil.copytree(root/'.openai',out/'.openai')
manifest=json.loads((out/'dist/.openai/hosting.json').read_text());assert manifest['d1']=='DB' and 'static' not in manifest
assert (out/'dist/client/index.html').exists();assert (out/'dist/server/index.js').exists();assert list((out/'dist/.openai/drizzle').glob('*.sql'))
print(out)
