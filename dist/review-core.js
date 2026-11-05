(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.AUDReview=factory()})(typeof globalThis!=='undefined'?globalThis:this,()=>{
'use strict';
const POT='Potencialmente qualificada',INC='Enquadramento incerto',NONE='Sem enquadramento identificado';
function signature(p){return JSON.stringify(p.registros_origem.map(r=>[r.docente_id,r.categoria_lattes,r.subcategoria_lattes,r.ano,r.referencia_original]).sort((a,b)=>JSON.stringify(a)<JSON.stringify(b)?-1:JSON.stringify(a)>JSON.stringify(b)?1:0))}
function status(p,r){return !r||r.action==='reverted'?'nao_revisado':r.source_signature!==signature(p)?'conflito':r.action}
function dataset(data,reviews,mode='automatic'){
 const products=data.produtos.map(p=>{
  const r=reviews[p.produto_id],state=status(p,r),confirmed=state==='confirmed';
  const automatic={estado:p.estado,grande_categoria:p.grande_categoria,tipo_capes:p.tipo_capes,justificativa:p.justificativa,regra:p.regra};
  const base={...p,revisao_gt:state,confirmada_gt:confirmed,decisao_gt:r||null,classificacao_automatica:automatic};
  if(mode==='automatic'||state==='nao_revisado')return base;
  if(state==='conflito')return{...base,estado:INC,justificativa:p.justificativa+' A fonte mudou desde a decisão humana; decisão preservada, mas aplicação pendente de nova conferência.'};
  if(confirmed){const general=data.catalogo[r.kind]?.escopo==='lista_geral_nao_equiparada';return{...base,estado:general?INC:POT,grande_categoria:r.category,tipo_capes:r.kind,tipo_bibliografico:data.catalogo[r.kind]?.tipo_bibliografico||p.tipo_bibliografico,escopo_documental:data.catalogo[r.kind]?.escopo||p.escopo_documental,justificativa:(general?'Tipo da lista geral confirmado no GT; recorte específico AU ainda não demonstrado. ':'')+r.notes,regra:'GT-MANUAL',necessita_conferencia:true,potencial_a_confirmar:general}};
  return{...base,estado:state==='rejected'?NONE:INC,justificativa:r.notes,regra:'GT-MANUAL'};
 });
 return{...data,produtos:mode==='confirmed'?products.filter(p=>p.confirmada_gt):products};
}
return{signature,status,dataset};
});
