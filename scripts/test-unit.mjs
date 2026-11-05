import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
for(const args of [['tests/test_cohort.cjs'],['tests/test_indicadores.cjs'],['tests/test_revisao_orientacoes.cjs'],['--test','tests/server.test.mjs']]){
 const r=spawnSync(process.execPath,args,{cwd:root,stdio:'inherit'});
 if(r.error){console.error(r.error.message);process.exit(1)}
 if(r.status!==0)process.exit(r.status||1);
}
