import {defineConfig} from 'vite';
import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const appRoot=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const repoRoot=resolve(appRoot,'..');

function git(args){
  try{return execFileSync('git',args,{cwd:repoRoot,encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim()}catch{return ''}
}

function buildInfo(){
  let version='0.0.0-dev';
  try{version=JSON.parse(readFileSync(resolve(repoRoot,'version.json'),'utf8')).version||version}catch{}
  return {version,commit:git(['rev-parse','HEAD'])||'unknown',dirty:Boolean(git(['status','--porcelain'])),built_at:new Date().toISOString()};
}

// Installed copies have no Git history, so every build stamps the identity it was made from.
const build=buildInfo();
try{writeFileSync(resolve(appRoot,'build-info.json'),JSON.stringify(build,null,2)+'\n')}catch{}

export default defineConfig({server:{proxy:{'/api':'http://127.0.0.1:8765'}},build:{outDir:'dist'}});
