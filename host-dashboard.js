const HOST_API="https://uggi-ray-aquaduse-host.onrender.com";

const $=id=>document.getElementById(id);
const stream=$("stream");

function addEvent(text){
  if(!stream)return;
  const e=document.createElement("div");
  e.className="event";
  e.textContent=`[${new Date().toLocaleTimeString()}] ${text}`;
  stream.prepend(e);
}

function setText(id,value){
  const el=$(id);
  if(el)el.textContent=value;
}

async function getJSON(path){
  const r=await fetch(HOST_API+path,{cache:"no-store"});
  if(!r.ok)throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

async function refreshHost(){
  try{
    const h=await getJSON("/api/health");
    addEvent(`HOST ONLINE • ${h.host||"Aquaduse Host"} • SAFE • v${h.version||"1.0.0"}`);
  }catch(e){
    addEvent(`HOST CONNECTION ERROR • ${e.message}`);
  }
}

async function refreshState(){
  try{
    const d=await getJSON("/api/state");
    const s=d.state||d;

    if(typeof s.water_level==="number")setText("water",s.water_level.toFixed(2));
    if(typeof s.water==="number")setText("water",s.water.toFixed(2));
    if(typeof s.chaos==="number")setText("chaos",s.chaos.toFixed(2));
    if(typeof s.temperature==="number")setText("temp",s.temperature.toFixed(2)+"°C");
    if(typeof s.temp==="number")setText("temp",s.temp.toFixed(2)+"°C");
    if(typeof s.generation==="number")setText("gen",s.generation);
    if(typeof s.gen==="number")setText("gen",s.gen);
  }catch(e){
    addEvent(`STATE ERROR • ${e.message}`);
  }
}

async function sendCommand(command){
  const cmd=String(command).toUpperCase();

  addEvent(`${cmd} | AUTHORIZATION: PENDING | EXECUTION: BLOCKED`);

  try{
    const r=await fetch(HOST_API+"/api/command",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        command:cmd,
        source:"UGGI-RAY Host Dashboard"
      })
    });

    if(!r.ok){
      addEvent(`${cmd} • BACKEND REJECTED • ${r.status}`);
      return;
    }

    addEvent(`${cmd} • RECORDED BY LIVE HOST • SAFE MODE`);
  }catch(e){
    addEvent(`${cmd} • CONNECTION ERROR • ${e.message}`);
  }
}

document.querySelectorAll("[data-a]").forEach(button=>{
  button.onclick=()=>sendCommand(button.dataset.a);
});

refreshHost();
refreshState();

setInterval(refreshHost,10000);
setInterval(refreshState,2000);
