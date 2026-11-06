// Editable composition for Figma file 4Yvy8L4twIYWW8f0dqUdz3.
// Run through use_figma; example values are design fixtures, never live signals.
const createdNodeIds = [];
const keep = node => { createdNodeIds.push(node.id); return node; };
const page = await figma.getNodeByIdAsync('0:1');
await figma.setCurrentPageAsync(page);
if (page.children.some(n => n.name === 'V3 · Canonical signal states')) {
  throw new Error('Design already exists; inspect before replacing it.');
}
await Promise.all(['Regular','Medium','Bold'].map(style => figma.loadFontAsync({family:'Roboto',style})));
const variables = {};
for (const [role,key] of Object.entries({
  background:'084fd9eef53493f628f937becb5914405009aa93',
  surface:'39429ef475465b43ef4cb71db29f18b87b4abf4a',
  muted:'2669a52b8e7217f9819767cb22af92e9332d8148',
  ink:'3955ea91dec6375cafc103197d010e8f972b48ea',
  accent:'ab44bc59c2465ccbd1e7e0f9df6c12a0e217b867',
  onAccent:'12167be5f8b2411f2a12385cd1f219300616a455'
})) variables[role] = await figma.variables.importVariableByKeyAsync(key);
const bodyStyle = await figma.importStyleByKeyAsync('1e92164361231ef1ed79f8fd256e78e0f6fbf250');
const paint = role => figma.variables.setBoundVariableForPaint({type:'SOLID',color:{r:0,g:0,b:0}},'color',variables[role]);
const fontLoads = new Map();
async function loadTree(root) {
  for (const node of root.findAllWithCriteria({types:['TEXT']})) {
    for (const segment of node.getStyledTextSegments(['fontName'])) {
      const key = JSON.stringify(segment.fontName);
      if (!fontLoads.has(key)) fontLoads.set(key,figma.loadFontAsync(segment.fontName));
    }
  }
  await Promise.all([...fontLoads.values()]);
}
function stack(parent,name,width,gap=12,role=null,padding=0) {
  const node=keep(figma.createAutoLayout('VERTICAL',{name,itemSpacing:gap,
    paddingTop:padding,paddingBottom:padding,paddingLeft:padding,paddingRight:padding}));
  parent.appendChild(node);
  node.resize(width,1); node.layoutSizingVertical='HUG';
  node.fills=role?[paint(role)]:[];
  return node;
}
function text(parent,characters,size=14,weight='Regular',role='ink',width=null) {
  const node=keep(figma.createText());parent.appendChild(node);
  node.fontName={family:'Roboto',style:weight};
  node.textStyleId=bodyStyle.id;
  node.fontName={family:'Roboto',style:weight};node.fontSize=size;
  node.lineHeight={unit:'PERCENT',value:138};
  node.characters=characters;node.name=characters.split('\n')[0].slice(0,65);
  node.fills=[paint(role)];
  node.resize(width||parent.width-parent.paddingLeft-parent.paddingRight,1);
  node.textAutoResize='HEIGHT';node.layoutSizingVertical='HUG';
  return node;
}
function row(parent,left,right,width=302) {
  const frame=keep(figma.createAutoLayout('HORIZONTAL',{name:left,itemSpacing:12,
    primaryAxisAlignItems:'SPACE_BETWEEN',counterAxisAlignItems:'CENTER'}));
  parent.appendChild(frame);frame.resize(width,1);frame.layoutSizingVertical='HUG';frame.fills=[];
  text(frame,left,13,'Regular','muted',126);
  const value=text(frame,right,14,'Medium','ink',width-138);value.textAlignHorizontal='RIGHT';
  return frame;
}
const cards=await figma.importComponentSetByKeyAsync('a79bb6c8ccfee2be2b9d5cefcb81fc2d88c62fff');
const buttonsSet=await figma.importComponentSetByKeyAsync('ab924dce8b851fd820bd0d56da24a9c489311ae6');
const cardMaster=cards.children.find(n=>n.name==='Style=Filled, Layout=Slot');
const buttonMaster=buttonsSet.children.find(n=>n.name==='Type=Round, Size=Small, State=Enabled');
await loadTree(cardMaster);await loadTree(buttonMaster);
async function card(parent,name) {
  const instance=keep(cardMaster.createInstance());
  parent.appendChild(instance);instance.name=name;
  await loadTree(instance);
  instance.resize(342,1);instance.layoutSizingVertical='HUG';
  const slot=instance.findOne(n=>n.type==='SLOT');
  if(!slot)throw new Error('Imported card has no content slot');
  for(const child of [...slot.children])child.remove();
  slot.layoutMode='VERTICAL';slot.primaryAxisSizingMode='AUTO';slot.counterAxisSizingMode='FIXED';
  slot.paddingTop=20;slot.paddingBottom=20;slot.paddingLeft=20;slot.paddingRight=20;
  slot.itemSpacing=12;slot.resize(342,1);slot.layoutSizingVertical='HUG';
  return {instance,slot};
}
async function button(parent,label) {
  const instance=keep(buttonMaster.createInstance());parent.appendChild(instance);
  await loadTree(instance);
  instance.setProperties({'Label text#58653:0':label,'Show icon#58653:51':false});
  instance.resize(342,48);instance.name=label;
  return instance;
}
const startX=Math.max(0,...page.children.map(n=>n.x+n.width))+100;
const board=stack(page,'V3 · Canonical signal states',1282,28,'surface',32);
board.x=startX;board.y=80;
text(board,'Semnalul trebuie înțeles dintr-o privire.',34,'Bold','ink',1218);
text(board,'V3 · Fără scor · Etape distincte · Timp validat separat de studiul simulat',16,'Regular','muted',1218);
text(board,'EXEMPLE DE INTERFAȚĂ — valorile de mai jos sunt demonstrative; nu reprezintă semnale live sau calibrare validată.',12,'Medium','muted',1218);
const states=[
 {name:'01 · PRE',stage:'PRE',eyebrow:'01 / 03 · URMĂREȘTE',title:'Oportunitate în urmărire',
  sub:'Nu intra încă. Așteaptă un OPEN_NOW valid.',time:'Așteaptă CONFIRM',status:'Condiții observate',
  action:'Vezi de ce urmărim',note:'Poate fi anulată dacă piața se schimbă.'},
 {name:'02 · CONFIRM',stage:'CONFIRM',eyebrow:'02 / 03 · PREGĂTEȘTE-TE',title:'Condiții reconfirmate',
  sub:'Pregătește-te. Intrarea încă nu este autorizată.',time:'Așteaptă OPEN_NOW',status:'Reevaluare validă',
  action:'Vezi explicația',note:'Expirare de execuție indisponibilă. Calibrarea este în colectare.'},
 {name:'03 · OPEN_NOW validat — exemplu',stage:'OPEN_NOW',eyebrow:'03 / 03 · INTRARE',title:'Fereastră de intrare',
  sub:'Exemplu pentru cazul cu expirare validată.',time:'3 min de la intrare',status:'Expirare validată · exemplu',
  action:'Vezi condițiile',note:'Timpul de execuție trebuie să provină din calibrarea aprobată. Niciun rezultat nu este garantat.'},
 {name:'04 · OPEN_NOW studiu',stage:'STUDIU V3',eyebrow:'OBSERVARE · FĂRĂ EXECUȚIE',title:'Simulare pe cotații reale',
  sub:'OPEN_NOW de studiu. Durata nu este validată pentru execuție.',time:'3 min · durată simulată',status:'Calibrare în colectare',
  action:'Deschide studiul',note:'Nu este un trade executat. Direcția și bufferul se măsoară separat la expirare.'},
 {name:'05 · Anulare',stage:'ANULAT',eyebrow:'OPORTUNITATE ÎNCHISĂ',title:'Spațiu insuficient',
  sub:'Piața nu mai oferă spațiul necesar în direcția urmărită.',time:'Fără intrare',status:'Motiv: structură invalidă',
  action:'Vezi motivul anulării',note:'Simbolul rămâne urmărit. O oportunitate nouă, distinctă, nu are pauză de cinci minute.'},
 {name:'06 · Rezultat studiu',stage:'REZULTAT',eyebrow:'OBSERVAȚIE LA EXPIRARE',title:'Direcție favorabilă',
  sub:'Exemplu: prețul a crescut, dar marja cerută nu a fost atinsă.',time:'13:13:32 UTC · exemplu',status:'Simulare · rezultat observat',
  action:'Vezi observațiile',note:'WIN pentru direcție nu înseamnă buffer atins. Rezultatul studiului nu este profit realizat.'}
];
const screens=[];const buttons=[];
for(let group=0;group<2;group++) {
  const grid=keep(figma.createAutoLayout('HORIZONTAL',{name:'Rând '+(group+1),itemSpacing:24,
    counterAxisAlignItems:'MIN'}));board.appendChild(grid);grid.fills=[];
  for(const state of states.slice(group*3,group*3+3)) {
    const screen=stack(grid,state.name,390,18,'background',24);screen.cornerRadius=28;
    text(screen,'13:09                                      EXEMPLE UI',12,'Medium','muted',342);
    text(screen,'TRADING SIGNALS',13,'Bold','ink',342);
    text(screen,'Semnale / EUR/USD',13,'Regular','muted',342);
    const badge=stack(screen,state.stage,342,0,'accent',10);badge.cornerRadius=12;
    text(badge,state.eyebrow,12,'Bold','onAccent',322);
    text(screen,state.title,28,'Bold','ink',342);
    text(screen,state.sub,15,'Regular','muted',342);
    const main=await card(screen,state.stage+' · datele semnalului');
    text(main.slot,'EUR/USD',26,'Bold','ink',302);
    text(main.slot,'↑ CREȘTERE · BUY / CALL',16,'Bold','ink',302);
    text(main.slot,'ID EUR-001 · aceeași idee între etape',11,'Regular','muted',302);
    row(main.slot,'Preț de referință','1.10020');
    row(main.slot,'Emis la','13:10:32 UTC');
    row(main.slot,'Analiză','M1');
    row(main.slot,state.stage==='STUDIU V3'?'Expirare simulată':'Timp / acțiune',state.time);
    row(main.slot,'Buffer urmărit','0.00008 unități de preț');
    text(main.slot,'Buffer = marja de deplasare urmărită. Nu garantează rezultatul.',12,'Regular','muted',302);
    const context=stack(screen,'Starea și explicația',342,8,'surface',16);context.cornerRadius=16;
    text(context,state.status,14,'Medium','ink',310);
    if(state.stage==='REZULTAT') {
      row(context,'Direcție la expirare','WIN',310);
      row(context,'Buffer la expirare','NEATINS',310);
    } else text(context,state.note,13,'Regular','muted',310);
    const action=await button(screen,state.action);buttons.push(action);
    text(screen,state.stage==='OPEN_NOW'?'Exemplu UI · nu confirmă existența unei calibrări live.':'Același simbol: oportunități distincte permise. Alte simboluri: atenție de 2 min.',11,'Regular','muted',342);
    const nav=stack(screen,'Navigare',342,0,'surface',12);nav.cornerRadius=14;
    text(nav,'Semnale                 Studii                 Cont',13,'Medium','ink',318);
    screens.push(screen);
  }
}
const notes=stack(board,'Contract și studiu comparativ',1218,12,'background',24);notes.cornerRadius=20;
text(notes,'Cum verificăm primul, al doilea și al treilea semnal',24,'Bold','ink',1170);
text(notes,'Ferestre fixe de 10 minute pe același simbol. Comparăm rezultatele observate pe poziții, cu numărul exact de cazuri. UNKNOWN și studiile suprapuse rămân separate; o pierdere nu crește automat șansa următorului semnal.',15,'Regular','muted',1170);
text(notes,'Contract: PRE = urmărește · CONFIRM = pregătește-te · OPEN_NOW = intrare numai cu timp validat · STUDIU = simulare explicită · ANULAT = motiv clar.',14,'Medium','ink',1170);
text(notes,'Surse: TELEGRAM_UX_v2.0.1 §5–9 · SIGNAL_EVENT / Execution Time · V3_SCORELESS_OWNER_AMENDMENT_v1.1.0 · V3_FOCUS_AND_SIGNAL_PRESENTATION_OWNER_AMENDMENT_v1.0.0',12,'Regular','muted',1170);
for(const action of buttons) await action.setReactionsAsync([{trigger:{type:'ON_CLICK'},actions:[{
  type:'NODE',destinationId:notes.id,navigation:'SCROLL_TO',transition:null,preserveScrollPosition:false
}]}]);
figma.viewport.scrollAndZoomIntoView([board]);
return {createdNodeIds,boardId:board.id,screens:screens.map(n=>({id:n.id,name:n.name,width:n.width,height:n.height})),
        editableTextCount:board.findAllWithCriteria({types:['TEXT']}).length,
        libraryInstances:board.findAllWithCriteria({types:['INSTANCE']}).length,
        exampleData:true,allNodesEditable:true};
