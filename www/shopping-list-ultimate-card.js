class ShoppingListUltimateCard extends HTMLElement {
  setConfig(config) { this.config = config; this.quantity = 1; this.product = null; this.render(); }
  set hass(hass) { this._hass = hass; if (!this._rendered) this.render(); this.renderRecent(); }
  getCardSize() { return 5; }
  render() {
    this._rendered = true;
    this.innerHTML = `<ha-card header="Shopping List Ultimate"><style>
      .body{padding:0 16px 16px}.scan{width:100%;min-height:56px;font-size:17px;background:var(--primary-color);color:var(--text-primary-color);border:0;border-radius:12px;cursor:pointer}
      video{width:100%;margin-top:12px;border-radius:12px;display:none}.product{display:none;grid-template-columns:88px 1fr;gap:14px;margin-top:16px}.product img{width:88px;height:88px;object-fit:contain;border-radius:10px;background:var(--secondary-background-color)}
      .qty{display:flex;align-items:center;gap:14px;margin:14px 0}.qty button,.add{min-width:44px;min-height:44px;border:0;border-radius:10px;background:var(--secondary-background-color);color:var(--primary-text-color)}.add{width:100%;background:var(--primary-color);color:var(--text-primary-color)}
      .error{color:var(--error-color);margin:10px 0}.manual{display:flex;gap:8px;margin-top:10px}.manual ha-textfield{flex:1}.recent{margin-top:18px}.recent-item{display:flex;align-items:center;gap:10px;padding:9px 0;cursor:pointer;border-top:1px solid var(--divider-color)}.recent-item img{width:42px;height:42px;object-fit:contain}.recent-item small{display:block;color:var(--secondary-text-color)}
    </style><div class="body"><button class="scan">📷 Product scannen</button><video playsinline muted></video><div class="error"></div>
    <div class="manual"><ha-textfield label="Barcode handmatig"></ha-textfield><ha-button>Opzoeken</ha-button></div>
    <div class="product"><img><div><h3></h3><div class="meta"></div><div class="qty"><button class="minus">−</button><b>1</b><button class="plus">+</button></div></div><button class="add">Toevoegen</button></div><div class="recent"><h3>Recente producten</h3><div class="recent-list"></div></div></div></ha-card>`;
    this.querySelector('.scan').onclick = () => this.scan();
    this.querySelector('.manual ha-button').onclick = () => this.lookup(this.querySelector('ha-textfield').value);
    this.querySelector('.minus').onclick = () => this.setQuantity(Math.max(1, this.quantity - 1));
    this.querySelector('.plus').onclick = () => this.setQuantity(this.quantity + 1);
    this.querySelector('.add').onclick = () => this.add(); this.renderRecent();
  }
  error(message) { this.querySelector('.error').textContent = message; }
  setQuantity(value) { this.quantity = value; this.querySelector('.qty b').textContent = value; }
  async scan() {
    this.error('');
    if (!navigator.mediaDevices?.getUserMedia) return this.error('Geen camera beschikbaar. Voer de barcode handmatig in.');
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}});
      const video = this.querySelector('video'); video.srcObject = this.stream; video.style.display = 'block'; await video.play();
      this.scanning = true;
      if ('BarcodeDetector' in window) {
        const detector = new BarcodeDetector({formats:['ean_13','ean_8','upc_a','upc_e']});
        const loop = async () => { if (!this.scanning) return; const codes = await detector.detect(video); if (codes[0]) { await this.found(codes[0].rawValue); return; } requestAnimationFrame(loop); }; loop();
      } else {
        await this.loadZxing();
        const reader = new ZXingBrowser.BrowserMultiFormatReader();
        this.controls = await reader.decodeFromVideoElement(video, (result) => { if (result) this.found(result.getText()); });
      }
    } catch (err) { this.stop(); this.error(err.name === 'NotAllowedError' ? 'Cameratoegang is geweigerd.' : 'Camera kon niet worden gestart.'); }
  }
  loadZxing() { if (window.ZXingBrowser) return Promise.resolve(); return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='/local/shopping-list-ultimate-zxing.min.js';s.onload=resolve;s.onerror=()=>reject(new Error('Lokale barcodebibliotheek ontbreekt.'));document.head.appendChild(s);}); }
  async found(code) { const now=Date.now(); if(this.lastCode===code && now-this.lastFound<3000) return; this.lastCode=code;this.lastFound=now;this.stop();await this.lookup(code); }
  stop() { this.scanning = false; this.controls?.stop(); this.controls=null; this.stream?.getTracks().forEach(t => t.stop()); const v=this.querySelector('video'); if(v) v.style.display='none'; }
  async lookup(barcode) {
    if (!barcode) return; this.error('Product opzoeken…');
    try { const result = await this._hass.callService('shopping_list_ultimate','lookup_barcode',{barcode}, {}, true); this.product=result.response?.product; if(!this.product) return this.unknown(barcode); this.showProduct(); }
    catch (err) { this.error(err.message || 'Product kon niet worden opgezocht.'); }
  }
  unknown(barcode) {
    this.error('Barcode onbekend');
    const name = prompt(`Barcode ${barcode}\nProductnaam:`); if (!name) return;
    const category = prompt('Categorie (optioneel):') || '';
    this._hass.callService('shopping_list_ultimate','add_product',{barcode,name,category}, {}, true).then(r=>{this.product=r.response?.product;this.showProduct();});
  }
  showProduct() { this.error(''); const p=this.product, el=this.querySelector('.product'); el.style.display='grid'; el.querySelector('img').src=p.image||''; el.querySelector('h3').textContent=p.custom_name||p.name||p.barcode; el.querySelector('.meta').textContent=[p.brand,p.quantity].filter(Boolean).join(' · '); }
  async add() { try { await this._hass.callService('shopping_list_ultimate','add_barcode',{barcode:this.product.barcode,quantity:this.quantity,todo_entity:this.config.todo_entity}, {}, true); this.error('Toegevoegd aan de boodschappenlijst.'); } catch(err) { this.error(err.message||'Toevoegen is mislukt.'); } }
  renderRecent() { const root=this.querySelector?.('.recent-list'); if(!root||!this._hass)return; const state=this._hass.states['sensor.shopping_list_ultimate_known_products']; const products=state?.attributes?.recent_products||[]; root.innerHTML=products.map((p,i)=>`<div class="recent-item" data-i="${i}"><img src="${p.image||''}"><div>${p.custom_name||p.name||p.barcode}<small>${p.scan_count||0} scans · ${p.last_scanned?new Date(p.last_scanned).toLocaleString():''}</small></div></div>`).join(''); root.querySelectorAll('.recent-item').forEach(el=>el.onclick=()=>{this.product=products[Number(el.dataset.i)];this.setQuantity(1);this.showProduct();this.add();}); }
  disconnectedCallback(){this.stop();}
}
customElements.define('shopping-list-ultimate-card', ShoppingListUltimateCard);
window.customCards=window.customCards||[];window.customCards.push({type:'shopping-list-ultimate-card',name:'Shopping List Ultimate',description:'Scan boodschappenbarcodes en voeg producten toe aan een todo-lijst.'});
