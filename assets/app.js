
const PRODUCTS = [
 {id:"dyazo",name:"Dyazo 2 in 1 Laptop & Mobile Stand",store:"Amazon",price:999,mrp:2199,rating:4.4,reviews:265,category:"electronics",image:"assets/dyazo-stand.png",affiliate:"https://link.amazon/B0eClibCt",deal:"55% OFF"},
 {id:"boat",name:"boAt Wireless Headphones",store:"Amazon",price:1999,mrp:4999,rating:4.4,reviews:12000,category:"electronics",image:"assets/dyazo-stand.png",affiliate:"#",deal:"60% OFF"},
 {id:"sony",name:"Sony Wireless Headphones",store:"Amazon",price:2999,mrp:5999,rating:4.6,reviews:8500,category:"electronics",image:"assets/dyazo-stand.png",affiliate:"#",deal:"50% OFF"},
 {id:"sneaker",name:"Everyday Casual Sneakers",store:"Flipkart",price:1299,mrp:2499,rating:4.3,reviews:1800,category:"fashion",image:"assets/dyazo-stand.png",affiliate:"#",deal:"48% OFF"}
];

const history = [2199,2099,1999,1899,1799,1699,1599,1499,1399,1299,1199,1099,999];

function money(n){return "₹"+n.toLocaleString("en-IN")}
function card(p){
 return `<article class="card">
  <div class="thumb"><img src="${p.image}" alt="${p.name}"></div>
  <div class="body">
   <div class="store">${p.store}</div><div class="title">${p.name}</div>
   <div class="prices"><span class="price">${money(p.price)}</span><span class="old">${money(p.mrp)}</span><span class="off">${p.deal}</span></div>
   <div class="rating">★ ${p.rating}/5 · ${p.reviews.toLocaleString("en-IN")} ratings</div>
   <div class="card-actions"><a class="btn" href="product.html?id=${p.id}">Compare</a><a class="btn alt" href="${p.affiliate}" target="_blank" rel="nofollow sponsored noopener">Buy</a></div>
  </div>
 </article>`
}
function render(list=PRODUCTS){document.querySelector("#products").innerHTML=list.length?list.map(card).join(""):`<div class="empty">No matching products found.</div>`}
function search(){
 const q=document.querySelector("#q").value.trim().toLowerCase();
 const cat=document.querySelector(".chip.active")?.dataset.cat||"all";
 render(PRODUCTS.filter(p=>(cat==="all"||p.category===cat)&&(!q||p.name.toLowerCase().includes(q)||p.store.toLowerCase().includes(q))));
}
document.addEventListener("DOMContentLoaded",()=>{
 render();
 document.querySelector("#q").addEventListener("input",search);
 document.querySelector("#searchBtn").addEventListener("click",search);
 document.querySelectorAll(".chip").forEach(c=>c.addEventListener("click",()=>{document.querySelectorAll(".chip").forEach(x=>x.classList.remove("active"));c.classList.add("active");search()}));
 const chart=document.querySelector("#chart");
 if(chart) chart.innerHTML=history.map(v=>`<span class="bar ${v===999?"low":""}" style="height:${Math.max(12,((v-800)/1500)*100)}%" title="${money(v)}"></span>`).join("");
});
