const state={products:[],category:'all',query:''};
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const money=n=>'₹'+Number(n||0).toLocaleString('en-IN');
const functionUrl=()=>`${String(window.ZENGHUNT_CONFIG?.supabaseUrl||'').replace(/\/$/,'')}/functions/v1/track-product`;
function img(url,name){return `<img src="${esc(url||'')}" alt="${esc(name)}" loading="lazy" onerror="this.onerror=null;this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22600%22 height=%22450%22%3E%3Crect width=%22100%25%22 height=%22100%25%22 fill=%22%23f7f8fa%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23939aa1%22 font-family=%22Arial%22 font-size=%2220%22%3ENo image%3C/text%3E%3C/svg%3E'">`}
function normalize(p){
  const listings=(p.product_listings||[]).map(l=>{
    const prices=(l.prices||[]).sort((a,b)=>new Date(b.checked_at)-new Date(a.checked_at));
    const latest=prices[0];
    return {...l,store:l.stores||{},latest};
  }).filter(l=>l.latest && Number(l.latest.price)>0);
  const best=listings.slice().sort((a,b)=>a.latest.price-b.latest.price)[0];
  if(!best) return {...p,listings,store:'',price:0,mrp:0,discount:0,buyUrl:'#',image:p.image_url};
  const price=Number(best.latest.price),mrp=Number(best.latest.mrp||0);
  const discount=Number(best.latest.discount_percent ?? (mrp>price ? ((mrp-price)/mrp*100):0));
  return {...p,listings,store:best.store.name||'Store',price,mrp,discount:Math.round(discount),buyUrl:best.product_url,image:p.image_url||best.image_url};
}
function card(p){return `<article class="card"><div class="pic">${img(p.image,p.name)}</div><div class="body"><div class="store">${esc(p.store)} · ${p.listings.length} store${p.listings.length===1?'':'s'}</div><div class="name">${esc(p.name)}</div><div><span class="price">${money(p.price)}</span>${p.mrp?` <span class="mrp">${money(p.mrp)}</span>`:''}${p.discount?` <span class="off">${p.discount}% OFF</span>`:''}</div><div class="rating">Live price data · ${p.listings.length} offer${p.listings.length===1?'':'s'}</div><div class="actions"><a class="btn compare" href="product.html?id=${encodeURIComponent(p.id)}">Price history</a><a class="btn" href="${esc(p.buyUrl)}" target="_blank" rel="nofollow sponsored noopener">Buy →</a></div></div></article>`}
function render(){const q=state.query.trim().toLowerCase();const list=state.products.filter(p=>(state.category==='all'||String(p.category||'').toLowerCase()===state.category)&&(!q||(p.name+' '+(p.brand||'')+' '+(p.category||'')+' '+p.listings.map(l=>l.store.name).join(' ')).toLowerCase().includes(q)));$('#count').textContent=`${list.length} products`;$('#grid').innerHTML=list.length?list.map(card).join(''):`<div class="empty">No live products match this search yet.</div>`}
async function load(){try{$('#grid').innerHTML='<div class="empty">Loading live products…</div>';const rows=await ZenGhuntAPI.getProducts();state.products=rows.map(normalize).filter(p=>p.listings.length);render()}catch(e){console.error(e);$('#grid').innerHTML='<div class="empty">Could not connect to ZenGhunt API. Check the Supabase project and publishable key.</div>'}}
async function trackProduct(){
  const input=$('#productUrl');
  const status=$('#trackStatus');
  const button=$('#trackBtn');
  const url=input.value.trim();
  if(!url){status.hidden=false;status.textContent='Paste a product URL first.';return;}
  button.disabled=true;
  button.textContent='Checking…';
  status.hidden=false;
  status.textContent='Reading the product page…';
  try{
    const cfg=window.ZENGHUNT_CONFIG||{};
    const response=await fetch(functionUrl(),{method:'POST',headers:{'Content-Type':'application/json',apikey:cfg.supabasePublishableKey,Authorization:`Bearer ${cfg.supabasePublishableKey}`},body:JSON.stringify({url})});
    const data=await response.json();
    if(!response.ok||!data.ok) throw new Error(data.error||`Tracker request failed (${response.status})`);
    const p=data.product||{};
    status.innerHTML=`<strong>${esc(p.name||'Product found')}</strong>${p.price!=null?` · ${money(p.price)}`:''} · ${esc(p.store||'Store')}<br><span>${esc(data.note||'Product page read successfully.')}</span>`;
    if(p.name) input.value='';
  }catch(e){
    console.error(e);
    status.textContent=e.message||'Unable to track this product.';
  }finally{
    button.disabled=false;
    button.textContent='Track Product';
  }
}
document.addEventListener('click',e=>{const b=e.target.closest('.filter');if(b){document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.category=b.dataset.cat;render()}const q=e.target.closest('[data-q]');if(q){state.query=q.dataset.q;$('#search').value=state.query;render();$('#deals').scrollIntoView({behavior:'smooth'})}if(e.target.id==='searchBtn'){state.query=$('#search').value;render();$('#deals').scrollIntoView({behavior:'smooth'})}if(e.target.id==='trackBtn') trackProduct()});
document.addEventListener('input',e=>{if(e.target.id==='search'){state.query=e.target.value;render()}});
load();
