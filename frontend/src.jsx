import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const currency = new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'});
const money = n => currency.format(Number(n)/100);
const monetary = new Set(['net','balance','income','expense','change']);
const names = {
  totals:'Ledger totals', monthly_flow:'Monthly cash flow', account_balances:'Account balances',
  spending_by_category:'Spending by category', income_sources:'Income sources', recent_entries:'Recent entries',
  daily_flow:'Daily cash flow', running_balance:'Running balance', largest_expenses:'Largest expenses',
  monthly_change:'Change since previous recorded month', category_frequency:'Entries by category',
  monthly_spending_rank:'Monthly category rankings'
};
async function fetchJson(path, opts) {
  const r=await fetch(path,opts);
  if(!r.ok) {const d=await r.json().catch(()=>null);throw Error(typeof d?.detail==='string'? d.detail : 'Request failed ('+r.status+').');}
  return r.json();
}
function App(){
  const [data,setData]=useState(null),[options,setOptions]=useState(null),[report,setReport]=useState('recent_entries');
  const [error,setError]=useState(''),[busy,setBusy]=useState(false),[adding,setAdding]=useState(false);
  const [notice,setNotice]=useState(''); const retry=useRef(null);
  async function load(){
    const [d,o]=await Promise.all([fetchJson('/api/dashboard'),fetchJson('/api/options')]);
    setData(d);setOptions(o);
  }
  useEffect(()=>{load().catch(e=>setError(e.message));},[]);
  async function submit(e){
    e.preventDefault(); if(busy)return;
    const form=e.currentTarget, f=new FormData(form);
    const amount=String(f.get('amount'));
    if(!/^\d+(\.\d{1,2})?$/.test(amount)){setError('Enter rupees with up to two decimal places.');return;}
    const [rupees,paise='']=amount.split('.');
    const body={posted:f.get('posted'),account_id:Number(f.get('account')),category_id:Number(f.get('category')),
      note:String(f.get('note')).trim(),amount_minor:Number(rupees)*100+Number(paise.padEnd(2,'0'))};
    if(!body.note || body.amount_minor<1){setError('Enter a description and a positive amount.');return;}
    const signature=JSON.stringify(body);
    if(retry.current?.signature!==signature)retry.current={signature,key:crypto.randomUUID()};
    setBusy(true);setError('');setNotice('');
    try{
      await fetchJson('/api/entries',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({...body,request_key:retry.current.key})});
      await load();retry.current=null;setAdding(false);setReport('recent_entries');setNotice('Entry saved.');
    }catch(e){setError(e.message);}finally{setBusy(false);}
  }
  const rows=data?.[report]||[],months=data?.monthly_flow.slice(-6)||[];
  const max=Math.max(1,...months.flatMap(m=>[Number(m.income),Number(m.expense)]));
  return <main><header><div><p className="eyebrow">PERSONAL FINANCE</p><h1>Analytical Ledger</h1></div>
    <button disabled={!options||busy} onClick={()=>{setAdding(!adding);setError('');setNotice('');}}>{adding?'Close form':'Add entry'}</button></header>
    {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
    {adding&&<form onSubmit={submit}><h2>New entry</h2><div className="fields">
      <label>Date<input name="posted" type="date" required defaultValue={new Date().toLocaleDateString('en-CA')}/></label>
      <label>Account<select aria-label="Account" name="account">{options.accounts.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
      <label>Category<select aria-label="Category" name="category">{options.categories.map(c=><option key={c.id} value={c.id}>{c.name} · {c.kind}</option>)}</select></label>
      <label>Amount (₹)<input name="amount" inputMode="decimal" required placeholder="0.00"/></label>
      <label>Description<input name="note" required maxLength="120"/></label></div><button disabled={busy}>{busy?'Saving…':'Save entry'}</button></form>}
    {!data&&!error&&<p>Loading ledger…</p>}
    {data&&<><section className="metrics">{[['balance','Net balance'],['income','Total income'],['expense','Total spending']].map(([k,label])=>
      <article key={k}><span>{label}</span><strong>{money(data.totals[0][k])}</strong></article>)}</section>
      <section className="flow"><h2>Monthly cash flow</h2><div className="legend">Income <i/> Spending <b/></div>
      {months.map(m=><div key={m.month} className="month"><span>{m.month}</span><div className="bars">
      <div className="in" style={{width:(100*m.income/max)+'%'}}/><div className="out" style={{width:(100*m.expense/max)+'%'}}/></div>
      <small>{money(m.income)} in · {money(m.expense)} out</small></div>)}{months.length===0&&<p>Add an entry to see monthly cash flow.</p>}</section>
      <section className="table"><div className="tablehead"><h2>Reports</h2><label>View <select aria-label="View" value={report} onChange={e=>setReport(e.target.value)}>{Object.entries(names).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label></div>
      {rows.length?<div className="scroll"><table><thead><tr>{Object.keys(rows[0]).map(k=><th key={k}>{k.replaceAll('_',' ')}</th>)}</tr></thead>
      <tbody>{rows.map((row,i)=><tr key={i}>{Object.entries(row).map(([k,v])=><td key={k}>{v==null?'—':monetary.has(k)?money(v):String(v)}</td>)}</tr>)}</tbody></table></div>:<p>No entries in this report.</p>}</section></>}
  </main>
}
createRoot(document.getElementById('root')).render(<App/>);
